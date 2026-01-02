"""
Service xử lý logic chatbot với chat history và lệnh tùy chỉnh
"""
from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Q
from openai import OpenAI

from apps.booking.models import Booking
from apps.chat.models import ChatSession, ChatMessage
from apps.sport_center.models import SportField
from apps.user.models import User
from apps.utils.enum_type import SportTypeEnum, StatusFieldEnum

client = OpenAI(api_key=settings.FPT_API_KEY, base_url=settings.FPT_URL_API)

SYSTEM_CONTEXT = """
Bạn là chatbot hỗ trợ khách hàng của trang web DaiHiep Sport.

DaiHiep Sport là nền tảng đặt sân thể thao trực tuyến nhanh chóng và tiện lợi khu vực thành phố Đà Nẵng (cũ).
Người dùng có thể:
- Tìm thông tin sân thể thao (bóng đá, cầu lông, tennis, pick-a-ball)
- Tìm sân trống theo khung giờ cụ thể
- Đặt sân trực tiếp theo khung giờ quy định của mỗi sân
- Lọc hoặc tìm sân theo khu vực địa lý, khung giờ hoặc môn thể thao
- Gợi ý sân gần nhất, rẻ nhất hoặc phù hợp nhất theo nhu cầu

Khi trả lời:
- Giữ phong cách thân thiện, tự nhiên, không quá máy móc
- Ưu tiên trả lời ngắn gọn, rõ ràng
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
"""

COMMAND_INFO = "/info"
COMMAND_HISTORY = "/history"

SPORT_TYPE_LABELS = {
    SportTypeEnum.FOOTBALL.value: "Bóng đá",
    SportTypeEnum.BADMINTON.value: "Cầu lông",
    SportTypeEnum.TENNIS.value: "Tennis",
    SportTypeEnum.PICK_A_BALL.value: "Pick-a-ball",
}


@dataclass
class ChatCommandContext:
    command_name: str
    ai_prompt: str
    system_messages: List[str]


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


def _format_price(value: Optional[Any]) -> str:
    if value is None:
        return "Giá chưa được cập nhật"

    try:
        normalized = int(float(value))
        return f"{normalized:,}đ"
    except (TypeError, ValueError):
        return "Giá không xác định"


def _extract_district(address: Optional[str]) -> Optional[str]:
    if not address:
        return None

    parts = [part.strip() for part in address.split(",") if part.strip()]
    return parts[-1] if parts else None


def _describe_field(field_data: Dict[str, Any]) -> str:
    center = field_data.get("sport_center") or "Trung tâm chưa rõ"
    address = field_data.get("address") or "Địa chỉ chưa rõ"
    sport_type = field_data.get("sport_type")
    sport_type_label = SPORT_TYPE_LABELS.get(sport_type, sport_type or "Loại sân")
    price = _format_price(field_data.get("price"))
    status = field_data.get("status", "Trạng thái chưa rõ")
    return (
        f"{field_data.get('name')} tại {center} | "
        f"{sport_type_label} | {address} | {price} | {status}"
    )


def search_sport_fields(query: Optional[str], limit: int = 5) -> List[Dict[str, Any]]:
    qs = SportField.objects.filter(status=StatusFieldEnum.ACTIVE).select_related("sport_center")

    if query:
        query_value = query.strip()
        query_upper = query_value.upper()
        filters = Q()
        filters |= Q(name__icontains=query_value)
        filters |= Q(address__icontains=query_value)
        filters |= Q(sport_center__name__icontains=query_value)
        if query_upper in SportTypeEnum.list():
            filters |= Q(sport_type=query_upper)

        qs = qs.filter(filters)

    qs = qs.order_by("price")[:limit]

    results = []
    for field in qs:
        results.append({
            "id": field.id,
            "name": field.name,
            "sport_center": field.sport_center.name if field.sport_center else None,
            "address": field.address,
            "sport_type": field.sport_type,
            "price": field.price,
            "status": field.status,
        })

    return results


def _find_nearby_field(fields: List[Dict[str, Any]], address: Optional[str]) -> Optional[Dict[str, Any]]:
    if not address:
        return None

    district = _extract_district(address)
    if not district:
        return None

    district_lower = district.lower()
    for field in fields:
        if field.get("address") and district_lower in field["address"].lower():
            return field

    return fields[0] if fields else None


def build_info_command_messages(
    query: Optional[str],
    user: Optional[User],
    fields: List[Dict[str, Any]]
) -> List[str]:
    lines = []
    search_term = query.strip() if query else "tất cả sân"
    lines.append(f"Lệnh /info kích hoạt với từ khóa: \"{search_term}\".")
    if user:
        lines.append(
            f"Thông tin user: {user.full_name or user.username} - Địa chỉ: {user.address or 'Chưa có'}."
        )
    else:
        lines.append("User hiện tại chưa đăng nhập (mảng user bị None).")

    if fields:
        lines.append("Danh sách sân phù hợp:")
        for idx, field in enumerate(fields, start=1):
            lines.append(f"{idx}. {_describe_field(field)}")

        nearby = _find_nearby_field(fields, user.address if user else None)
        if nearby:
            district = _extract_district(user.address if user else None)
            location_label = f" (gần {district})" if district else ""
            lines.append(
                f"Gợi ý sân gần người dùng{location_label}: {_describe_field(nearby)}"
            )
    else:
        lines.append("Không tìm thấy sân nào phù hợp với yêu cầu.")

    return ["\n".join(lines)]


def build_history_command_messages(
    user: Optional[User],
    booking_history: List[Dict[str, Any]]
) -> List[str]:
    lines = []
    lines.append("Lệnh /history được gọi để hiển thị lịch sử đặt sân của người dùng.")

    if user:
        lines.append(f"User hiện tại: {user.full_name or user.username}.")
    else:
        lines.append("Không thể xác định user để lấy lịch sử.")

    if booking_history:
        lines.append("Danh sách booking gần nhất:")
        for idx, booking in enumerate(booking_history, start=1):
            sport_field = booking.get("sport_field", {})
            lines.append(
                f"{idx}. {sport_field.get('name') or 'Sân không rõ'} | "
                f"Ngày: {booking.get('booking_date') or 'Chưa xác định'} | "
                f"Khung giờ: {booking.get('rental_slot') or 'Chưa xác định'} | "
                f"Giá: {booking.get('price') or 'Chưa xác định'} | "
                f"Trạng thái: {booking.get('status') or 'Không rõ'}"
            )
    else:
        lines.append("Chưa có booking nào được lưu.")

    return ["\n".join(lines)]


def parse_chat_command(message: str) -> Optional[Dict[str, str]]:
    text = (message or "").strip()
    if not text.startswith("/"):
        return None

    parts = text.split(maxsplit=1)
    command = parts[0].lower()

    if command not in {COMMAND_INFO, COMMAND_HISTORY}:
        return None

    argument = parts[1].strip() if len(parts) > 1 else ""
    return {"command": command, "argument": argument}


def build_command_context(
    message: str,
    user: Optional[User],
    booking_history: Optional[List[Dict[str, Any]]]
) -> Optional[ChatCommandContext]:
    parsed = parse_chat_command(message)
    if not parsed:
        return None

    command_name = parsed["command"]
    argument = parsed.get("argument", "")
    system_messages: List[str] = []

    if command_name == COMMAND_INFO:
        fields = search_sport_fields(argument)
        system_messages = build_info_command_messages(argument, user, fields)
        ai_prompt = argument or "Bạn có thể giới thiệu vài sân nổi bật ở Đà Nẵng?"
    elif command_name == COMMAND_HISTORY:
        bookings = booking_history or []
        system_messages = build_history_command_messages(user, bookings)
        ai_prompt = "Cho tôi biết lịch sử booking gần nhất của tôi"
    else:
        return None

    return ChatCommandContext(
        command_name=command_name,
        ai_prompt=ai_prompt,
        system_messages=system_messages,
    )


def build_messages(
    question: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    booking_history: Optional[List[Dict]] = None,
    command_context: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Xây dựng danh sách messages để gửi đến API
    Bao gồm: system context, booking history, chat history, và câu hỏi hiện tại
    """
    messages = []
    
    # System context
    messages.append({"role": "system", "content": SYSTEM_CONTEXT})
    
    # Booking history nếu có
    if booking_history:
        booking_info = json.dumps(booking_history, ensure_ascii=False, default=str)
        messages.append({
            "role": "system",
            "content": f"Lịch sử đặt sân của người dùng (gần nhất): {booking_info}"
        })

    if command_context:
        for context in command_context:
            messages.append({"role": "system", "content": context})
    
    # Chat history từ database (chỉ lấy các message trước câu hỏi hiện tại)
    if chat_history:
        # Chỉ lấy các message trước đó, không bao gồm câu hỏi hiện tại
        messages.extend(chat_history)
    
    # Câu hỏi hiện tại
    messages.append({"role": "user", "content": question})
    
    return messages


def ask_chatbot(
    question: str,
    session: ChatSession,
    booking_history: Optional[List[Dict]] = None,
    command_context: Optional[List[str]] = None
) -> str:
    """
    Gọi API chatbot với chat history đầy đủ
    
    Args:
        question: Câu hỏi của user
        session: ChatSession object
        booking_history: Lịch sử booking (optional)
        command_context: Thông tin hệ thống bổ sung từ command
    
    Returns:
        Câu trả lời từ chatbot
    """
    # Load chat history từ database
    chat_history = load_chat_history(session)
    
    # Xây dựng messages
    messages = build_messages(question, chat_history, booking_history, command_context)
    
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
        
        return resp.choices[0].message.content
    
    except Exception as e:
        return f"Lỗi khi gọi chatbot: {str(e)}"

