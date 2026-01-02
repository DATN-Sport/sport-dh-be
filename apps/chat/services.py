"""
Service xử lý logic chatbot với chat history và lệnh tùy chỉnh
"""
from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional
from datetime import date
from collections import defaultdict

from django.conf import settings
from openai import OpenAI

from apps.booking.models import Booking
from apps.chat.models import ChatSession, ChatMessage
from apps.sport_center.models import SportField
from apps.user.models import User
from apps.utils.enum_type import StatusBookingEnum, StatusFieldEnum

client = OpenAI(api_key=settings.FPT_API_KEY, base_url=settings.FPT_URL_API)

SYSTEM_CONTEXT = """
Bạn là chatbot hỗ trợ khách hàng của trang web DaiHiep Sport.

DaiHiep Sport là nền tảng đặt sân thể thao trực tuyến nhanh chóng và tiện lợi khu vực thành phố Đà Nẵng.
Người dùng có thể:
- Tìm thông tin sân thể thao (bóng đá, cầu lông, tennis, pick-a-ball)
- Tìm sân trống theo khung giờ cụ thể
- Đặt sân trực tiếp qua chatbot hoặc theo khung giờ quy định của mỗi sân
- Lọc hoặc tìm sân theo khu vực địa lý (quận như Hải Châu, Liên Chiểu, Cẩm Lệ, Ngũ Hành Sơn, Sơn Trà, Hòa Vang), khung giờ hoặc môn thể thao
- Gợi ý sân gần nhất, rẻ nhất hoặc phù hợp nhất theo nhu cầu

Khi trả lời:
- Giữ phong cách thân thiện, tự nhiên, không quá máy móc
- Ưu tiên trả lời NGẮN GỌN, SÚC TÍCH, không dài dòng
- KHÔNG xuống dòng nhiều, chỉ xuống dòng khi cần thiết
- Nếu người dùng hỏi chung chung (ví dụ "cho tôi tìm sân trống tối nay"), hãy hỏi lại để làm rõ thông tin cần thiết
- Không trả lời ngoài phạm vi thể thao hoặc dịch vụ đặt sân
- Nhớ ngữ cảnh từ các câu hỏi trước đó trong cuộc trò chuyện

Luôn nhớ rằng bạn là trợ lý AI của DaiHiep Sport.

Khi bạn nhận thêm dữ liệu `booking_history`, đó là danh sách các booking gần nhất gồm các trường:
 - `id`: mã booking
 - `price`: giá booking
 - `booking_date`: ngày booking
 - `status`: trạng thái booking (PENDING/CONFIRMED/COMPLETED/CANCELLED)
 - `rental_slot`: thông tin khung giờ gồm `time_slot`
 - `sport_field`: thông tin sân gồm `id`, `name`, `address`, `sport_type`, và `sport_center`
 - `sport_center`: thông tin trung tâm trong `sport_field` gồm `id`, `name`

Khi bạn nhận dữ liệu `available_bookings`, đó là danh sách các sân trống (booking PENDING) có cấu trúc:
[
  {
    "sport_center": {
      "id": số,
      "name": "Tên trung tâm",
      "address": "Địa chỉ đầy đủ",
      "owner": "UUID của chủ sở hữu"
    },
    "sport_field": [
      {
        "id": số,
        "name": "Tên sân (ví dụ: A1, A2)",
        "sport_type": "FOOTBALL/BADMINTON/TENNIS/PICK_A_BALL",
        "rental_slot": ["07:30 - 08:30", "10:30 - 11:30", ...]  // Danh sách các khung giờ TRỐNG (CHỈ từ booking PENDING của sân này)
      },
      ...
    ],
    "booking_date": "YYYY-MM-DD",
    "status": "PENDING",
    "price": số (giá tiền)
  },
  ...
]

LƯU Ý: `rental_slot` trong mỗi `sport_field` là danh sách khung giờ trống CHỈ từ các booking PENDING của sân đó. Mỗi sân có danh sách rental_slot riêng.

QUAN TRỌNG về dữ liệu available_bookings:
- `rental_slot` trong mỗi `sport_field` là danh sách các KHUNG GIỜ TRỐNG (có thể đặt được) - CHỈ từ booking PENDING của sân đó
- Mỗi phần tử trong `rental_slot` là một chuỗi thời gian dạng "HH:MM - HH:MM" (ví dụ: "14:00 - 15:00")
- Mỗi khung giờ là 1 giờ (1 slot), KHÔNG phải khung giờ liên tục nhiều giờ
- `booking_date` trong mỗi entry là ngày của các booking PENDING đó
- Khi người dùng hỏi về sân trống, bạn PHẢI:
  1. Xác định ngày họ hỏi (nếu họ nói "hôm nay", "ngày mai", "hôm qua" thì bạn cần biết ngày hiện tại là gì - ngày hiện tại sẽ được cung cấp trong system message)
  2. Lọc available_bookings theo booking_date phù hợp
  3. Lọc theo khu vực/địa chỉ nếu người dùng yêu cầu
  4. Lọc theo khung giờ nếu người dùng yêu cầu - QUAN TRỌNG:
     - Khi người dùng hỏi "6h đến 8h tối" hoặc "6h hoặc 8h tối", họ đang hỏi về các KHUNG GIỜ RIÊNG LẺ trong khoảng đó
     - Ví dụ: "6h đến 8h tối" = hỏi các khung giờ: 18:30, 19:30, 20:30 (nếu có)
     - Ví dụ: "6h hoặc 8h tối" = hỏi khung giờ 18:30 HOẶC 20:30 (nếu có)
     - KHÔNG phải hỏi về khung giờ liên tục 2-3 giờ
     - Tìm các rental_slot có thời gian bắt đầu trong khoảng đó (ví dụ: 18:00-20:59 cho "6h đến 8h tối")
  5. TRẢ LỜI CỤ THỂ VÀ NGẮN GỌN: Liệt kê từng trung tâm, từng sân và khung giờ trống
     - Liệt kê thời gian BẮT ĐẦU trên 1 dòng, cách nhau bằng dấu phẩy: "06:30, 07:30, 08:30, 09:30..."
     - KHÔNG liệt kê cả khung giờ đầy đủ (ví dụ: "06:30 - 07:30"), chỉ cần thời gian bắt đầu
     - KHÔNG xuống dòng nhiều, format ngắn gọn
     - Ví dụ: "Sân bóng đá Mini Hòa Xuân: A1 (06:30, 07:30, 08:30, 10:30), A2 (06:30, 07:30, 08:30, 09:30)"
  6. Nếu không tìm thấy, trả lời: "Không có sân nào trống trong khung giờ/khu vực này"
- KHÔNG được trả lời chung chung kiểu "có sân trống" mà phải liệt kê cụ thể từng trung tâm, từng sân và khung giờ

Khi người dùng muốn đặt sân, bạn cần hướng dẫn họ:
  - Người dùng chỉ cần nhắn: "tôi đặt [tên trung tâm] lúc [khung giờ] - xác nhận"
  - Ví dụ: "tôi đặt Sân bóng đá Mini Hòa Xuân lúc 17:30 - 18:30 - xác nhận"
  - KHÔNG cần chọn cụ thể sân (A1, A2, A3...), hệ thống sẽ tự động lấy sân đầu tiên trống khung giờ đó
  - Phải có cụm "- xác nhận" thì hệ thống mới tiến hành đặt sân
  - Tên trung tâm phải khớp với tên trong danh sách sân trống
  - Khung giờ phải đúng format "HH:MM - HH:MM" (ví dụ: "17:30 - 18:30")
  - Khi trả lời về sân trống, bạn PHẢI gợi ý format đặt sân: "Để đặt sân, bạn vui lòng nhắn: 'Tôi đặt [tên trung tâm] lúc [khung giờ] - xác nhận'"
  - Ví dụ gợi ý: "Để đặt sân, bạn vui lòng nhắn: 'Tôi đặt Sân bóng đá Mini Hòa Xuân lúc 18:30 - 19:30 - xác nhận'"
  - KHÔNG được gợi ý format "Tôi đặt [Tên sân] lúc [Khung giờ] - xác nhận" (sai - không dùng tên sân)
"""



def load_chat_history(session: ChatSession, limit: int = 20) -> List[Dict[str, str]]:
    """
    Load lịch sử chat từ database
    Trả về danh sách messages theo format OpenAI: [{"role": "user", "content": "..."}, ...]
    """
    messages = ChatMessage.objects.filter(session=session).order_by('created_at')[:limit]
    
    history = []
    for msg in messages:
        history.append({
            "role": msg.role,  # 'user' hoặc 'assistant'
            "content": msg.content
        })
    
    return history


def get_available_bookings(booking_date: Optional[str] = None, address_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lấy danh sách booking PENDING (sân trống)
    Format: sport_center -> sport_field[] -> rental_slot[]
    """
    try:
        # 1. Parse booking_date
        if booking_date:
            try:
                target_date = date.fromisoformat(booking_date)
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()

        # 2. Query booking PENDING của ngày được chọn, chỉ lấy sport_field ACTIVE
        bookings = Booking.objects.filter(
            status=StatusBookingEnum.PENDING.value,
            booking_date=target_date,
            sport_field__status=StatusFieldEnum.ACTIVE.value
        ).select_related(
            'sport_field',
            'sport_field__sport_center',
            'sport_field__sport_center__owner',
            'rental_slot'
        )

        # 3. Lọc theo địa chỉ nếu có
        if address_filter and address_filter.strip():
            bookings = bookings.filter(
                sport_field__sport_center__address__icontains=address_filter
            ) | bookings.filter(
                sport_field__address__icontains=address_filter
            )

        # 4. Group by (sport_center, booking_date) -> sport_field -> rental_slot
        # Structure: {(center_id, booking_date): {center_info, fields: {field_id: {field_info, slots: set()}}}}
        result_dict = {}
        
        for booking in bookings:
            # Validate
            if not booking.sport_field or not booking.sport_field.sport_center or not booking.rental_slot:
                continue
            
            sport_field = booking.sport_field
            sport_center = sport_field.sport_center
            rental_slot = booking.rental_slot
            
            # Key: (center_id, booking_date)
            key = (sport_center.id, booking.booking_date)
            
            # Khởi tạo center entry nếu chưa có
            if key not in result_dict:
                result_dict[key] = {
                    'sport_center': {
                        'id': sport_center.id,
                        'name': sport_center.name,
                        'address': sport_center.address,
                        'owner': str(sport_center.owner.id) if sport_center.owner else None,
                    },
                    'booking_date': booking.booking_date,
                    'price': booking.price,
                    'sport_fields': {}  # {field_id: {field_info, rental_slots: set()}}
                }
            
            # Khởi tạo field entry nếu chưa có
            field_id = sport_field.id
            if field_id not in result_dict[key]['sport_fields']:
                result_dict[key]['sport_fields'][field_id] = {
                    'id': sport_field.id,
                    'name': sport_field.name,
                    'sport_type': sport_field.sport_type,
                    'rental_slots': set()
                }
            
            # Thêm rental_slot vào set
            if rental_slot.time_slot:
                result_dict[key]['sport_fields'][field_id]['rental_slots'].add(rental_slot.time_slot)

        # 5. Chuyển đổi sang format response
        result = []
        for key, data in result_dict.items():
            # Chuyển sport_fields từ dict sang list
            sport_fields = []
            for field_id, field_data in data['sport_fields'].items():
                rental_slots = sorted(list(field_data['rental_slots']))
                if rental_slots:  # Chỉ thêm field nếu có rental_slot
                    sport_fields.append({
                        'id': field_data['id'],
                        'name': field_data['name'],
                        'sport_type': field_data['sport_type'],
                        'rental_slot': rental_slots,
                    })
            
            # Chỉ thêm center nếu có sport_field
            if sport_fields:
                result.append({
                    'sport_center': data['sport_center'],
                    'sport_field': sport_fields,
                    'booking_date': data['booking_date'].isoformat(),
                    'status': StatusBookingEnum.PENDING.value,
                    'price': data['price'],
                })

        return result
    except Exception as e:
        print(f"Error getting available bookings: {e}")
        return []


def build_messages(
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    booking_history: Optional[List[Dict]] = None,
    available_bookings: Optional[List[Dict]] = None,
) -> List[Dict[str, str]]:
    """
    Xây dựng danh sách messages để gửi đến API
    Bao gồm: system context, booking history, available bookings, chat history, và câu hỏi hiện tại
    """
    from datetime import date
    
    messages = []
    
    # System context
    messages.append({"role": "system", "content": SYSTEM_CONTEXT})
    
    # Thông tin ngày hiện tại
    today = date.today()
    messages.append({
        "role": "system",
        "content": f"NGÀY HIỆN TẠI: {today.isoformat()} ({today.strftime('%d/%m/%Y')}). Khi người dùng hỏi 'hôm nay', 'ngày mai', 'hôm qua', bạn cần tính toán dựa trên ngày này."
    })
    
    # Available bookings (sân trống) - QUAN TRỌNG cho việc trả lời câu hỏi về sân trống
    if available_bookings:
        available_info = json.dumps(available_bookings, ensure_ascii=False, default=str, indent=2)
        messages.append({
            "role": "system",
            "content": f"Dữ liệu sân trống hiện tại (booking PENDING):\n{available_info}\n\nQUAN TRỌNG:\n- Mỗi entry có booking_date riêng, bạn PHẢI lọc theo booking_date phù hợp với câu hỏi của người dùng\n- `rental_slot` trong mỗi `sport_field` là danh sách khung giờ trống CHỈ từ booking PENDING của sân đó\n- Mỗi khung giờ là 1 giờ (1 slot), KHÔNG phải khung giờ liên tục nhiều giờ\n- Khi người dùng hỏi '6h đến 8h tối' hoặc '6h hoặc 8h tối', họ đang hỏi về các KHUNG GIỜ RIÊNG LẺ trong khoảng đó:\n  + '6h đến 8h tối' = hỏi các khung giờ: 18:30, 19:30, 20:30 (nếu có)\n  + '6h hoặc 8h tối' = hỏi khung giờ 18:30 HOẶC 20:30 (nếu có)\n  + KHÔNG phải hỏi về khung giờ liên tục 2-3 giờ\n  + Tìm các rental_slot có thời gian bắt đầu trong khoảng đó (ví dụ: 18:00-20:59 cho '6h đến 8h tối')\n- Khi trả lời, PHẢI liệt kê CỤ THỂ từng trung tâm, từng sân và khung giờ trống\n- KHÔNG được trả lời chung chung kiểu 'có sân trống' mà phải nêu rõ: tên trung tâm, tên sân và khung giờ\n- TRẢ LỜI NGẮN GỌN: Liệt kê thời gian BẮT ĐẦU trên 1 dòng, cách nhau bằng dấu phẩy (ví dụ: '06:30, 07:30, 08:30')\n- KHÔNG liệt kê cả khung giờ đầy đủ, chỉ cần thời gian bắt đầu\n- KHÔNG xuống dòng nhiều, format ngắn gọn\n- Ví dụ: 'Sân bóng đá Mini Hòa Xuân: A1 (06:30, 07:30, 08:30, 10:30), A2 (06:30, 07:30, 08:30, 09:30)'\n- Nếu không có dữ liệu phù hợp, hãy nói 'Không có sân nào trống'."
        })
    
    # Booking history nếu có
    if booking_history:
        booking_info = json.dumps(booking_history, ensure_ascii=False, default=str)
        messages.append({
            "role": "system",
            "content": f"Lịch sử đặt sân của người dùng (gần nhất): {booking_info}"
        })
    
    # Chat history từ database (chỉ lấy các message trước câu hỏi hiện tại)
    if chat_history:
        # Chỉ lấy các message trước đó, không bao gồm câu hỏi hiện tại
        messages.extend(chat_history)
    
    # Câu hỏi hiện tại
    messages.append({"role": "user", "content": question})
    
    return messages


def parse_user_booking_intent(question: str, available_bookings: Optional[List[Dict]] = None) -> Optional[Dict[str, Any]]:
    """
    Parse booking intent từ câu hỏi của user
    Format: "tôi đặt [tên trung tâm] lúc [khung giờ] - xác nhận"
    Ví dụ: "tôi đặt Sân bóng đá Mini Hòa Xuân lúc 17:30 - 18:30 - xác nhận"
    """
    import re
    from datetime import date
    
    if not question:
        return None
    
    # Kiểm tra có "- xác nhận" không
    if "- xác nhận" not in question.lower() and "xác nhận" not in question.lower():
        return None
    
    # Tìm pattern: "đặt [tên trung tâm] lúc [khung giờ]"
    # Pattern linh hoạt hơn để bắt nhiều format
    patterns = [
        r'(?:tôi|mình|cho tôi|đặt)\s+(.+?)\s+lúc\s+(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})',
        r'(?:đặt|book)\s+(.+?)\s+(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})',
    ]
    
    center_name = None
    rental_slot_time = None
    
    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            center_name = match.group(1).strip()
            rental_slot_time = match.group(2).strip()
            # Chuẩn hóa format thời gian (loại bỏ khoảng trắng thừa)
            rental_slot_time = re.sub(r'\s+', ' ', rental_slot_time)
            break
    
    if not center_name or not rental_slot_time:
        return None
    
    # Tìm trung tâm trong available_bookings
    booking_date = date.today()  # Mặc định hôm nay
    
    if available_bookings:
        for center_data in available_bookings:
            center = center_data.get('sport_center', {})
            center_name_from_data = center.get('name', '')
            
            # So khớp tên trung tâm (case-insensitive, có thể là substring)
            if center_name.lower() in center_name_from_data.lower() or center_name_from_data.lower() in center_name.lower():
                # Kiểm tra rental_slot trong sport_field có chứa time_slot này không
                sport_fields = center_data.get('sport_field', [])
                for field in sport_fields:
                    rental_slots = field.get('rental_slot', [])
                    if rental_slot_time in rental_slots:
                        # Lấy booking_date từ center_data
                        booking_date_str = center_data.get('booking_date')
                        if booking_date_str:
                            try:
                                booking_date = date.fromisoformat(booking_date_str)
                            except:
                                pass
                        
                        return {
                            'sport_center_id': center.get('id'),
                            'center_name': center_name_from_data,
                            'booking_date': booking_date.isoformat(),
                            'rental_slot_time': rental_slot_time,
                            'price': center_data.get('price', 0)
                        }
    
    return None


def parse_booking_intent(answer: str, available_bookings: Optional[List[Dict]] = None) -> Optional[Dict[str, Any]]:
    """
    Parse booking intent từ câu trả lời của AI
    Tìm pattern: BOOKING_CONFIRM: sport_field_id=..., booking_date=..., rental_slot_time=...
    Lưu ý: Format mới không có sport_field trong available_bookings, cần tìm từ database
    """
    import re
    
    if not answer or "BOOKING_CONFIRM:" not in answer:
        return None
    
    # Tìm pattern
    pattern = r'BOOKING_CONFIRM:\s*sport_field_id=(\d+),\s*booking_date=([\d-]+),\s*rental_slot_time=([\d:\s-]+)'
    match = re.search(pattern, answer)
    
    if not match:
        return None
    
    sport_field_id = int(match.group(1))
    booking_date_str = match.group(2)
    rental_slot_time = match.group(3).strip()
    
    # Tìm sport_field để verify
    sport_field = SportField.objects.filter(id=sport_field_id).select_related('sport_center').first()
    if not sport_field:
        return None
    
    # Verify với available_bookings nếu có
    if available_bookings:
        sport_center_id = sport_field.sport_center.id if sport_field.sport_center else None
        for center_data in available_bookings:
            center = center_data.get('sport_center', {})
            if center.get('id') == sport_center_id:
                # Kiểm tra rental_slot trong sport_field có chứa time_slot này không
                sport_fields = center_data.get('sport_field', [])
                for field in sport_fields:
                    if field.get('id') == sport_field_id:
                        rental_slots = field.get('rental_slot', [])
                        if rental_slot_time in rental_slots:
                            return {
                                'sport_field_id': sport_field_id,
                                'booking_date': booking_date_str,
                                'rental_slot_time': rental_slot_time,
                                'field_name': sport_field.name,
                                'center_name': sport_field.sport_center.name if sport_field.sport_center else '',
                                'price': center_data.get('price', 0)
                            }
        # Nếu không tìm thấy trong available_bookings, vẫn trả về để thử đặt (có thể đã hết)
        return {
            'sport_field_id': sport_field_id,
            'booking_date': booking_date_str,
            'rental_slot_time': rental_slot_time,
            'field_name': sport_field.name,
            'center_name': sport_field.sport_center.name if sport_field.sport_center else '',
            'price': 0
        }
    
    return {
        'sport_field_id': sport_field_id,
        'booking_date': booking_date_str,
        'rental_slot_time': rental_slot_time,
        'field_name': sport_field.name,
        'center_name': sport_field.sport_center.name if sport_field.sport_center else '',
        'price': 0
    }


def create_booking_from_intent(
    user: User,
    booking_intent: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Tạo booking từ intent đã parse
    Có 2 loại intent:
    1. Từ user: có sport_center_id, cần tìm sport_field đầu tiên trống
    2. Từ AI: có sport_field_id, dùng trực tiếp
    """
    try:
        from apps.booking.models import RentalSlot
        from apps.utils.enum_type import StatusBookingEnum
        from apps.sport_center.models import SportCenter
        
        booking_date_str = booking_intent['booking_date']
        rental_slot_time = booking_intent['rental_slot_time']
        
        # Parse date
        booking_date = date.fromisoformat(booking_date_str)
        
        # Tìm rental_slot theo time_slot
        rental_slot = RentalSlot.objects.filter(time_slot=rental_slot_time).first()
        if not rental_slot:
            return {'error': 'Không tìm thấy khung giờ'}
        
        # Nếu có sport_field_id, dùng trực tiếp
        if 'sport_field_id' in booking_intent:
            sport_field_id = booking_intent['sport_field_id']
            sport_field = SportField.objects.filter(id=sport_field_id).first()
            if not sport_field:
                return {'error': 'Không tìm thấy sân'}
        # Nếu có sport_center_id, tìm sport_field đầu tiên trống
        elif 'sport_center_id' in booking_intent:
            sport_center_id = booking_intent['sport_center_id']
            sport_center = SportCenter.objects.filter(id=sport_center_id).first()
            if not sport_center:
                return {'error': 'Không tìm thấy trung tâm'}
            
            # Tìm booking PENDING đầu tiên của trung tâm này với khung giờ này
            booking = Booking.objects.filter(
                sport_field__sport_center_id=sport_center_id,
                rental_slot=rental_slot,
                booking_date=booking_date,
                status=StatusBookingEnum.PENDING.value
            ).select_related('sport_field').order_by('sport_field__id').first()
            
            if not booking:
                return {'error': 'Không còn sân trống trong khung giờ này'}
            
            sport_field = booking.sport_field
        else:
            return {'error': 'Thiếu thông tin trung tâm hoặc sân'}
        
        # Tìm booking PENDING tương ứng (nếu chưa có từ trên)
        if 'sport_field_id' in booking_intent:
            booking = Booking.objects.filter(
                sport_field=sport_field,
                rental_slot=rental_slot,
                booking_date=booking_date,
                status=StatusBookingEnum.PENDING.value
            ).first()
            
            if not booking:
                return {'error': 'Sân này đã được đặt hoặc không còn trống'}
        
        # Update booking: set user và status = CONFIRMED
        booking.user = user
        booking.status = StatusBookingEnum.CONFIRMED.value
        booking.save()
        
        return {
            'success': True,
            'booking_id': booking.id,
            'sport_field_name': sport_field.name,
            'center_name': sport_field.sport_center.name if sport_field.sport_center else '',
            'booking_date': booking_date.isoformat(),
            'rental_slot': rental_slot_time,
            'price': booking.price
        }
    except Exception as e:
        return {'error': f'Lỗi khi đặt sân: {str(e)}'}


def ask_chatbot(
    question: str,
    session: ChatSession,
    booking_history: Optional[List[Dict]] = None,
    available_bookings: Optional[List[Dict]] = None,
    command_context: Optional[List[str]] = None,
    user: Optional[User] = None
) -> str:
    """
    Gọi API chatbot với chat history đầy đủ
    
    Args:
        question: Câu hỏi của user
        session: ChatSession object
        booking_history: Lịch sử booking (optional)
        available_bookings: Danh sách sân trống (optional)
        command_context: Thông tin hệ thống bổ sung (không dùng nữa, giữ để tương thích)
        user: User object để đặt sân nếu có intent
    
    Returns:
        Câu trả lời từ chatbot (có thể đã xử lý booking nếu có intent)
    """
    # Load chat history từ database
    chat_history = load_chat_history(session)
    
    # Xây dựng messages
    messages = build_messages(question, chat_history, booking_history, available_bookings)
    
    try:
        resp = client.chat.completions.create(
            model=settings.FPT_MODEL_NAME,
            messages=messages,
            temperature=0.8,
            max_tokens=2048,
            top_p=1,
            presence_penalty=0,
            frequency_penalty=0
        )
        
        answer = resp.choices[0].message.content
        
        # Kiểm tra xem có booking intent không
        booking_intent = parse_booking_intent(answer, available_bookings)
        if booking_intent and user:
            # Thực hiện đặt sân
            booking_result = create_booking_from_intent(user, booking_intent)
            
            if booking_result.get('success'):
                # Thay thế câu trả lời bằng thông báo thành công
                return (
                    f"✅ Đã đặt sân thành công!\n\n"
                    f"📅 Sân: {booking_result.get('sport_field_name')}\n"
                    f"🏟️ Trung tâm: {booking_result.get('center_name')}\n"
                    f"📆 Ngày: {booking_result.get('booking_date')}\n"
                    f"⏰ Khung giờ: {booking_result.get('rental_slot')}\n"
                    f"💰 Giá: {booking_result.get('price'):,.0f}đ\n\n"
                    f"Cảm ơn bạn đã sử dụng dịch vụ!"
                )
            else:
                # Giữ nguyên câu trả lời của AI nhưng thêm thông báo lỗi
                error_msg = booking_result.get('error', 'Không thể đặt sân')
                return f"{answer}\n\n⚠️ Lỗi: {error_msg}"
        
        return answer
    
    except Exception as e:
        return f"Lỗi khi gọi chatbot: {str(e)}"

