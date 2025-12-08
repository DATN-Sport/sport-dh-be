# API thống kê doanh thu/booking

Endpoint: `GET /api/booking/stats/`

- Quyền: `IsOwner` → ADMIN xem toàn bộ, OWNER chỉ xem dữ liệu sport_center do mình sở hữu.
- Auth: dùng JWT/cookie như các API khác (header `Authorization: Bearer <token>` hoặc cookie nếu đã đăng nhập).
- Múi giờ: mặc định `Asia/Ho_Chi_Minh`.

## Tham số query

| Tham số | Kiểu | Bắt buộc | Mô tả |
| --- | --- | --- | --- |
| `preset` | `today` \| `this_week` \| `this_month` \| `this_quarter` | Không | Ưu tiên dùng nếu không truyền `date_from`/`date_to`. Mặc định `this_month` nếu không truyền gì. |
| `date_from` | `YYYY-MM-DD` | Không | Ngày bắt đầu; nếu chỉ gửi một đầu, API tự gán đầu còn lại bằng cùng giá trị. |
| `date_to` | `YYYY-MM-DD` | Không | Ngày kết thúc; phải ≥ `date_from` nếu cả hai được truyền. |
| `statuses` | Danh sách chuỗi | Không | Mặc định tính `CONFIRMED`, `COMPLETED`. Truyền nhiều giá trị: `?statuses=CONFIRMED&statuses=COMPLETED` hoặc `statuses[]=...` tùy client. |
| `limit_top_fields` | Số nguyên 1-50 | Không | Giới hạn số sân trong `top_fields`, mặc định 5. |

Ghi chú: Nếu truyền cả `preset` và `date_from/date_to`, khoảng ngày sẽ ưu tiên `date_from/date_to`.

## Cấu trúc dữ liệu trả về

```json
{
  "filters": {
    "preset": "this_month",
    "date_from": "2025-02-01",
    "date_to": "2025-02-28",
    "statuses": ["CONFIRMED", "COMPLETED"],
    "limit_top_fields": 5
  },
  "summary": {
    "total_revenue": 1234000.0,
    "total_bookings": 42
  },
  "by_status": [
    {"status": "COMPLETED", "revenue": 900000.0, "count": 25},
    {"status": "CONFIRMED", "revenue": 334000.0, "count": 17}
  ],
  "by_center": [
    {
      "center_id": 1,
      "center_name": "DaiHiep Center 1",
      "revenue": 500000.0,
      "count": 15
    }
  ],
  "top_fields": [
    {
      "field_id": 10,
      "field_name": "Sân 7A",
      "center_id": 1,
      "center_name": "DaiHiep Center 1",
      "revenue": 300000.0,
      "count": 8
    }
  ]
}
```

## Ví dụ gọi API

### 1) Thống kê tháng hiện tại (mặc định)
```
GET /api/booking/stats/
Authorization: Bearer <token>
```

### 2) Khoảng ngày tùy chỉnh
```
GET /api/booking/stats/?date_from=2025-02-01&date_to=2025-02-15
```

### 3) Chỉ tính trạng thái CONFIRMED và giới hạn top 10 sân
```
GET /api/booking/stats/?statuses=CONFIRMED&limit_top_fields=10
```

### 4) Preset quý hiện tại
```
GET /api/booking/stats/?preset=this_quarter
```

## Lưu ý cho FE

- Danh sách `statuses` gửi dạng lặp query param (`?statuses=...`) hoặc `statuses[]` tùy client; DRF đều parse thành list.
- Nếu cần hiển thị cả doanh thu của booking chưa hoàn tất, FE truyền thêm các status khác (ví dụ `PENDING`, `CONFIRMED`).
- Số liệu theo `price` đã lưu trong `Booking`; không tự tính lại từ bảng sân.
- Chủ sân chỉ thấy trung tâm của mình; nếu FE dùng tài khoản chủ sân, không cần tự lọc thêm ở client.
- `total_revenue` luôn float, kể cả khi không có dữ liệu (sẽ trả `0.0`).
