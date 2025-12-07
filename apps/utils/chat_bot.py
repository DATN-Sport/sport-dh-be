from django.conf import settings
from openai import OpenAI
import json


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
"""

def ask_fpt(question: str, booking_history=None) -> str:
    if booking_history is None:
        booking_history = []

    messages = [
        {"role": "system", "content": SYSTEM_CONTEXT},
        {"role": "system", "content": f"Lịch sử đặt sân (gần nhất): {json.dumps(booking_history, ensure_ascii=False, default=str)}"},
        {"role": "assistant", "content": "Đã hiểu. Tôi là chatbot hỗ trợ khách hàng DaiHiep Sport."}]
    # user message
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
