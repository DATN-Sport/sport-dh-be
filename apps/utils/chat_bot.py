import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Max, Min
from openai import OpenAI

from apps.booking.models import Booking, RentalSlot
from apps.sport_center.models import SportCenter, SportField
from apps.utils.enum_type import SportTypeEnum, StatusFieldEnum


client = OpenAI(api_key=settings.FPT_API_KEY, base_url=settings.FPT_URL_API)

SYSTEM_CONTEXT_ANALYZE = """
Bạn là trợ lý AI của DaiHiep Sport, chỉ làm nhiệm vụ phân tích ý định và đặt câu hỏi bổ sung ngắn gọn, không trả lời nội dung chính.
- Đầu ra mong muốn: 1-2 câu hỏi ngắn để làm rõ các tham số còn thiếu (khu vực, môn, ngày, khung giờ, sân cụ thể, mức giá).
- Đừng trả lời dông dài; chỉ hỏi lại để thu thập đủ dữ liệu trước khi thực thi truy vấn.
- Nếu đã đủ thông tin, xác nhận ngắn gọn rằng đã đủ và có thể tra cứu.
"""

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
- Nếu người dùng hỏi chung chung (ví dụ “cho tôi tìm sân trống tối nay”), hãy hỏi lại để làm rõ thông tin cần thiết
- Không trả lời ngoài phạm vi thể thao hoặc dịch vụ đặt sân

Luôn nhớ rằng bạn là trợ lý AI của DaiHiep Sport.

Khi bạn nhận thêm dữ liệu `booking_history`, đó là danh sách các booking gần nhất gồm các trường:
 - `id`: mã booking
 - `price`: giá booking
 - `booking_date`: ngày booking
 - `status`: trạng thái booking (PENDING/CONFIRMED/COMPLETED/CANCELLED)
 - `rental_slot`: thông tin khung giờ gồm `time_slot`
 - `sport_field`: thông tin sân gồm `id`, `name`, `address`, `sport_type`, và `sport_center`
 - `sport_center`: thông tin trung tâm trong `sport_field` gồm `id`, `name`

Khi bạn nhận `data_summary` sau bước query, các dạng dữ liệu có thể gồm:
- `centers`: danh sách trung tâm, mỗi phần tử có `id`, `name`, `address`, kèm `fields`:
  - `fields`: mỗi sân có `id`, `name`, `address`, `sport_type`, `price`, `status`, có thể có `available_slots`, `booked_slots`.
- `slots`: danh sách khung giờ cho một sân cụ thể với `id`, `name`, `time_slot`, `is_booked`.
- `pricing`: thống kê giá với `min_price`, `max_price`, `avg_price`, và `sample_fields` minh họa.
- `bookings`: lịch sử/tra cứu booking đã được chuẩn hóa tương tự `booking_history`.

Ý định (intent) thường gặp: `availability_search`, `center_field_info`, `rental_slot_info`, `pricing_general`, `booking_history`. Hãy dựa vào intent và dữ liệu tóm tắt để trả lời ngắn gọn, chính xác, gợi ý hành động tiếp theo nếu cần.
"""

# ---- Intent & params helpers ----
INTENT_BOOKING_HISTORY = "booking_history"
INTENT_AVAILABILITY = "availability_search"
INTENT_CENTER_FIELD_INFO = "center_field_info"
INTENT_RENTAL_SLOT = "rental_slot_info"
INTENT_PRICING = "pricing_general"

SPORT_TYPE_KEYWORDS = {
    "bóng đá": SportTypeEnum.FOOTBALL,
    "football": SportTypeEnum.FOOTBALL,
    "cầu lông": SportTypeEnum.BADMINTON,
    "badminton": SportTypeEnum.BADMINTON,
    "tennis": SportTypeEnum.TENNIS,
    "pick": SportTypeEnum.PICK_A_BALL,
}

REQUIRED_FIELDS = {
    INTENT_AVAILABILITY: ["area", "sport_type", "date", "time_slot"],
    INTENT_BOOKING_HISTORY: [],
    INTENT_CENTER_FIELD_INFO: ["area"],
    INTENT_RENTAL_SLOT: ["sport_field_id", "date"],
    INTENT_PRICING: ["sport_type"],
}


def _detect_sport_type(text: str) -> Optional[str]:
    lowered = text.lower()
    for key, value in SPORT_TYPE_KEYWORDS.items():
        if key in lowered:
            return value
    return None


def _detect_date(text: str) -> Optional[date]:
    lowered = text.lower()
    if "hôm nay" in lowered:
        return date.today()
    if "ngày mai" in lowered or "mai" in lowered:
        return date.today() + timedelta(days=1)

    match = re.search(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year_part = match.group(3)
        year = int(year_part) if year_part else date.today().year
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _detect_time_slot(text: str) -> Optional[str]:
    match = re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return None


def _detect_area(text: str) -> Optional[str]:
    lowered = text.lower()
    if "hòa xuân" in lowered:
        return "Hòa Xuân"
    if "hòa khánh" in lowered:
        return "Hòa Khánh"
    match = re.search(r"khu vực\s+([\w\s]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def determine_intent(question: str) -> str:
    lowered = question.lower()
    if any(k in lowered for k in ["lịch sử", "đã đặt", "booking", "tình trạng"]):
        return INTENT_BOOKING_HISTORY
    if any(k in lowered for k in ["trống", "còn sân", "khung giờ", "slot", "còn không"]):
        return INTENT_AVAILABILITY
    if any(k in lowered for k in ["trung tâm", "danh sách sân", "ở khu vực", "có sân nào", "field"]):
        return INTENT_CENTER_FIELD_INFO
    if any(k in lowered for k in ["khung giờ sân", "slot sân", "lịch sân"]):
        return INTENT_RENTAL_SLOT
    if any(k in lowered for k in ["giá", "bao nhiêu", "mức phí", "rẻ nhất"]):
        return INTENT_PRICING
    # fallback
    return INTENT_BOOKING_HISTORY


def analyze_question(question: str) -> Dict[str, Any]:
    intent = determine_intent(question)
    params = {
        "area": _detect_area(question),
        "sport_type": _detect_sport_type(question),
        "date": _detect_date(question),
        "time_slot": _detect_time_slot(question),
        "price_lte": None,
        "sport_field_id": None,
    }
    missing = [field for field in REQUIRED_FIELDS.get(intent, []) if not params.get(field)]
    return {"intent": intent, "params": params, "missing": missing}


def build_missing_message(intent: str, missing_fields: List[str]) -> str:
    if not missing_fields:
        return ""
    readable = ", ".join(missing_fields)
    return f"Mình cần thêm thông tin: {readable}. Bạn cung cấp giúp để mình tra cứu nhanh và chính xác hơn?"


# ---- Data fetchers ----
def _serialize_booking(qs) -> List[Dict[str, Any]]:
    items = []
    for booking in qs:
        sport_field = booking.sport_field
        sport_center = sport_field.sport_center if sport_field else None
        items.append({
            "id": booking.id,
            "price": booking.price,
            "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
            "status": booking.status,
            "rental_slot": booking.rental_slot.time_slot if booking.rental_slot else None,
            "sport_field": {
                "id": sport_field.id,
                "name": sport_field.name,
                "address": sport_field.address,
                "sport_type": sport_field.sport_type,
                "sport_center": {
                    "id": sport_center.id,
                    "name": sport_center.name,
                } if sport_center else None,
            } if sport_field else None,
        })
    return items


def _fetch_booking_history(user) -> Dict[str, Any]:
    qs = Booking.objects.filter(user=user).select_related(
        "sport_field",
        "sport_field__sport_center",
        "rental_slot"
    ).order_by("-booking_date")[:10]
    return {"bookings": _serialize_booking(qs)}


def _fetch_center_and_fields(area: Optional[str], sport_type: Optional[str], price_lte: Optional[float]):
    centers = SportCenter.objects.all()
    if area:
        centers = centers.filter(address__icontains=area)
    centers_map: Dict[int, Dict[str, Any]] = {}
    for center in centers[:20]:
        centers_map[center.id] = {"id": center.id, "name": center.name, "address": center.address, "fields": []}

    fields = SportField.objects.select_related("sport_center").filter(status=StatusFieldEnum.ACTIVE.value)
    if centers_map:
        fields = fields.filter(sport_center_id__in=centers_map.keys())
    if sport_type:
        fields = fields.filter(sport_type=sport_type)
    if price_lte:
        fields = fields.filter(price__lte=price_lte)

    return centers_map, fields[:20]


def _fetch_availability(params: Dict[str, Any]) -> Dict[str, Any]:
    centers_map, fields = _fetch_center_and_fields(params.get("area"), params.get("sport_type"), params.get("price_lte"))
    if not fields:
        return {"centers": []}

    rental_slots = list(RentalSlot.objects.all())
    date_value = params.get("date")

    bookings = Booking.objects.filter(
        sport_field_id__in=[f.id for f in fields],
        booking_date=date_value
    ).select_related("rental_slot", "sport_field", "sport_field__sport_center")

    if params.get("time_slot"):
        bookings = bookings.filter(rental_slot__time_slot__icontains=params["time_slot"])

    bookings_by_field = {}
    for b in bookings:
        bookings_by_field.setdefault(b.sport_field_id, []).append(b)

    for field in fields:
        booked_slots = [bk.rental_slot.time_slot for bk in bookings_by_field.get(field.id, []) if bk.rental_slot]
        available_slots = [rs.time_slot for rs in rental_slots if rs.time_slot not in booked_slots]
        center_entry = centers_map.get(field.sport_center_id)
        if center_entry is None:
            continue
        center_entry["fields"].append({
            "id": field.id,
            "name": field.name,
            "address": field.address,
            "sport_type": field.sport_type,
            "price": field.price,
            "available_slots": available_slots,
            "booked_slots": booked_slots,
        })

    return {"centers": list(centers_map.values())}


def _fetch_center_field_info(params: Dict[str, Any]) -> Dict[str, Any]:
    centers_map, fields = _fetch_center_and_fields(params.get("area"), params.get("sport_type"), params.get("price_lte"))
    for field in fields:
        center_entry = centers_map.get(field.sport_center_id)
        if center_entry is None:
            continue
        center_entry["fields"].append({
            "id": field.id,
            "name": field.name,
            "address": field.address,
            "sport_type": field.sport_type,
            "price": field.price,
            "status": field.status,
        })
    return {"centers": list(centers_map.values())}


def _fetch_rental_slot_info(params: Dict[str, Any]) -> Dict[str, Any]:
    field_id = params.get("sport_field_id")
    date_value = params.get("date")
    if not field_id or not date_value:
        return {"slots": []}

    rental_slots = list(RentalSlot.objects.all())
    bookings = Booking.objects.filter(sport_field_id=field_id, booking_date=date_value).select_related("rental_slot")
    booked_slot_ids = {bk.rental_slot_id for bk in bookings if bk.rental_slot_id}

    slots = []
    for rs in rental_slots:
        slots.append({
            "id": rs.id,
            "name": rs.name,
            "time_slot": rs.time_slot,
            "is_booked": rs.id in booked_slot_ids,
        })
    return {"slots": slots}


def _fetch_pricing(params: Dict[str, Any]) -> Dict[str, Any]:
    qs = SportField.objects.filter(status=StatusFieldEnum.ACTIVE.value)
    if params.get("sport_type"):
        qs = qs.filter(sport_type=params["sport_type"])
    if params.get("area"):
        qs = qs.filter(address__icontains=params["area"])

    agg = qs.aggregate(min_price=Min("price"), max_price=Max("price"), avg_price=Avg("price"))
    sample = [
        {
            "id": f.id,
            "name": f.name,
            "address": f.address,
            "sport_type": f.sport_type,
            "price": f.price,
        }
        for f in qs[:5]
    ]
    return {"pricing": agg, "sample_fields": sample}


def fetch_intent_data(intent: str, params: Dict[str, Any], user) -> Dict[str, Any]:
    if intent == INTENT_AVAILABILITY:
        return _fetch_availability(params)
    if intent == INTENT_CENTER_FIELD_INFO:
        return _fetch_center_field_info(params)
    if intent == INTENT_RENTAL_SLOT:
        return _fetch_rental_slot_info(params)
    if intent == INTENT_PRICING:
        return _fetch_pricing(params)
    return _fetch_booking_history(user)


def _to_serializable_params(params: Dict[str, Any]) -> Dict[str, Any]:
    safe_params = {}
    for key, value in params.items():
        if isinstance(value, (date, datetime)):
            safe_params[key] = value.isoformat()
        else:
            safe_params[key] = value
    return safe_params


def ask_fpt(question: str, intent: Optional[str] = None, params: Optional[Dict[str, Any]] = None,
            data_summary: Optional[Dict[str, Any]] = None, booking_history=None,
            missing: Optional[List[str]] = None, stage: str = "final") -> str:
    if booking_history is None:
        booking_history = []
    params = params or {}
    messages = []

    if stage == "analyze":
        messages.append({"role": "system", "content": SYSTEM_CONTEXT_ANALYZE})
        if intent:
            messages.append({"role": "system", "content": f"Intent dự kiến: {intent}. Tham số đã nhận: {json.dumps(_to_serializable_params(params), ensure_ascii=False)}"})
        if missing:
            messages.append({"role": "system", "content": f"Các tham số còn thiếu cần hỏi thêm: {missing}"})
        messages.append({"role": "assistant", "content": "Hãy hỏi lại 1-2 câu ngắn để làm rõ các tham số còn thiếu. Nếu đã đủ, xác nhận ngắn gọn là đủ để tra cứu."})
        messages.append({"role": "user", "content": question})
    else:
        messages.append({"role": "system", "content": SYSTEM_CONTEXT})

        if intent:
            messages.append({"role": "system", "content": f"Phân loại yêu cầu: {intent}. Tham số đã hiểu: {json.dumps(_to_serializable_params(params), ensure_ascii=False)}"})

        if data_summary:
            messages.append({"role": "system", "content": f"Dữ liệu đã query (tóm tắt): {json.dumps(data_summary, ensure_ascii=False, default=str)}"})
        elif booking_history:
            messages.append({"role": "system", "content": f"Lịch sử đặt sân (gần nhất): {json.dumps(booking_history, ensure_ascii=False, default=str)}"})

        messages.append({"role": "assistant", "content": "Đã hiểu. Tôi là chatbot hỗ trợ khách hàng DaiHiep Sport."})
        messages.append({"role": "user", "content": question})

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
        return f"Lỗi khi gọi chatbot: {e}"
