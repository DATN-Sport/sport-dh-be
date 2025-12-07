## Mục tiêu
- Thiết kế quy trình chat 2 bước: (1) phân loại nghiệp vụ + thu thập đủ thông tin, (2) query dữ liệu tối thiểu rồi mới hỏi model để ra câu trả lời cuối.
- Giảm token cho model chính bằng cách chỉ gửi dữ liệu đã lọc, tập trung vào lịch sử booking, danh sách trung tâm/sân, và slot khả dụng.

## Nguồn dữ liệu & filter hiện có
- SportCenter: `id, owner, name, address` (filter: `owner`, `name__icontains`, `address__icontains`).
- SportField: `id, sport_center`, `name`, `address`, `sport_type`, `price`, `status` (filter: `sport_center`, `address__icontains`, `sport_center__name__icontains`, `sport_type`, `price`, `price__lte`, `status`).
- RentalSlot: `id, name, time_slot` (filter: `name__icontains`, `time_slot__icontains`).
- Booking: `id, user, sport_field, rental_slot, price, booking_date, status` (filter: `user`, `sport_field`, `rental_slot`, `price`, `booking_date` range, `status`, `month`, `year`). BookingManageFilter auto hạn chế theo owner khi user là OWNER.

## Phân loại intent (gợi ý 5 loại chính)
- `booking_history/status`: hỏi lịch sử, tình trạng booking. Query Booking (select_related field/center/slot) theo user (hoặc owner lọc theo sân thuộc mình), mặc định ngày hôm nay nếu không filter.
- `availability_search`: tìm sân trống theo khu vực/thời gian/môn thể thao/giá. Query SportCenter address ~ khu vực + SportField (sport_type, price, status=ACTIVE) rồi loại trừ Booking đã chiếm slot/time/date.
- `center_field_info`: hỏi danh sách trung tâm/sân theo khu vực, môn, giá, trạng thái. Dùng SportCenterFilter + SportFieldFilter (center_name/address/sport_type/price_lte/status).
- `rental_slot_info`: hỏi khung giờ mở bán, slot còn/đang dùng cho một sân. Query RentalSlot + Booking tại ngày/slot để biết đã bị đặt chưa.
- `pricing/offer/general`: hỏi giá tham khảo, quy tắc đặt/hủy, hướng dẫn. Không cần query nặng; có thể chỉ lấy giá/price_lte từ SportField hoặc trả lời tĩnh nếu thiếu dữ liệu.

## Câu hỏi mẫu để nhận diện intent
- “Lịch sử đặt sân của tôi tuần này thế nào?” → booking_history/status
- “Ở khu vực Hòa Xuân còn sân bóng đá trống lúc 18:00-20:00 hôm nay không?” → availability_search
- “Có trung tâm nào ở Hòa Khánh cho tennis giá dưới 200k không?” → center_field_info
- “Khung giờ sân A ngày mai còn slot nào?” → rental_slot_info
- “Giá sân bóng đá thường dao động bao nhiêu? Có quy định hủy không?” → pricing/offer/general

## Thông tin cần hỏi lại trước khi query (tối thiểu)
- availability_search: khu vực/phường, môn thể thao, ngày, khung giờ (hoặc rental_slot), ngân sách tối đa (tùy chọn), ưu tiên (gần/giá rẻ).
- booking_history/status: khoảng thời gian (ngày/tuần/tháng), trạng thái cần lọc (pending/confirmed/...), user muốn xem của mình hay (nếu owner) của sân nào.
- center_field_info: khu vực, môn, mức giá trần, trạng thái sân (active), số lượng kết quả mong muốn.
- rental_slot_info: sân nào (id/tên), ngày nào, khung giờ cụ thể hay muốn liệt kê tất cả.
- pricing/offer/general: môn thể thao, khu vực, yêu cầu khung giờ (để gợi ý giá thực tế thay vì trả lời chung chung).

## Chiến lược query theo intent
- booking_history/status: dùng `Booking.objects.filter(user=request.user)` hoặc owner auto set by filter; `select_related` sport_field->sport_center, rental_slot; mặc định `booking_date=today` nếu không có filter; giới hạn 10-20 bản ghi mới nhất.
- availability_search:
  - B1: tìm SportCenter `address__icontains=area`, có thể lọc thêm `name__icontains`.
  - B2: tìm SportField thuộc các center đó, filter `sport_type`, `price__lte`, `status=ACTIVE`.
  - B3: lấy các Booking của các field này theo `booking_date` và `rental_slot` khớp time_slot yêu cầu; loại trừ field đã bận; trả về danh sách field + số slot trống.
- center_field_info: SportCenterFilter + SportFieldFilter; nếu chỉ cần top N, áp dụng `order_by(price)` hoặc `?limit`.
- rental_slot_info: lấy tất cả RentalSlot; join Booking theo `booking_date` và `sport_field` để đánh dấu slot nào đã được đặt.
- pricing/offer/general: lấy min/max/avg price của SportField theo `sport_type`/`address__icontains`, nếu không đủ dữ liệu trả lời khái quát.

## Quy trình 2 bước gợi ý
- Bước 1 (Intent + thu thập tham số):
  - Phân loại intent dựa trên từ khóa/kết cấu câu hỏi (danh sách ở trên).
  - Hỏi lại các tham số còn thiếu (area/sport_type/date/time_slot/price cap/id sân...).
  - Khi đủ tham số, tạo plan query cụ thể (model, filter fields, limit).
- Bước 2 (Thực thi + trả lời):
  - Thực thi các query tối thiểu theo plan.
  - Chuẩn hóa dữ liệu tóm tắt (đếm slot trống, danh sách center/field, lịch sử booking).
  - Gửi model FPT lần cuối với: (a) SYSTEM_CONTEXT, (b) ý định + tham số đã chuẩn, (c) kết quả dữ liệu tóm tắt. Không gửi toàn bộ raw data dài.

## Ghi chú triển khai nhanh
- Tách hàm `build_intent_and_params(question)` → trả về intent + slots thiếu + plan query.
- Tách hàm `fetch_data(plan)` để thực hiện ORM/filter.
- Tóm tắt dữ liệu trước khi gửi model: chỉ gửi top N (ví dụ 5-10) và các trường: center(id,name,address), field(id,name,address,sport_type,price,status), booking(id,date,status,slot,time_slot,center/field names).
- Model call: chỉ sau khi có kết quả query hoặc đã hỏi đủ điều kiện; nếu thiếu dữ liệu, ưu tiên hỏi tiếp người dùng thay vì gọi model tốn token.

