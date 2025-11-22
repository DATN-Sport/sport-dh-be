import google.generativeai as genai

genai.configure(api_key="AIzaSyD5UUiMMULL6gzVw77aLO1UbKApQhvOnx4")

model = genai.GenerativeModel("gemini-flash-lite-latest")  # model free, nhẹ và nhanh

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
- Nếu người dùng hỏi chung chung (ví dụ “cho tôi tìm sân trống tối nay”), hãy hỏi lại để làm rõ thông tin cần thiết (môn thể thao, khu vực, giờ cụ thể, v.v.)
- Nếu có thể, hãy gợi ý tính năng để họ khám phá thêm (ví dụ: “bạn có thể dùng chức năng lọc theo khu vực để xem nhanh các sân gần nhất”)
- Không trả lời ngoài phạm vi thể thao hoặc dịch vụ đặt sân

Luôn nhớ rằng bạn là trợ lý AI của DaiHiep Sport, mục tiêu là giúp người dùng tìm và đặt sân nhanh nhất có thể.
"""

def ask_gemini(question: str, history=None, data_booking=None) -> str:
    if history is None:
        history = []

    messages = []

    # Thêm system context
    messages.append({"role": "user", "parts": [SYSTEM_CONTEXT]})
    messages.append({"role": "model", "parts": ["Đã hiểu. Tôi là chatbot hỗ trợ khách hàng DaiHiep Sport."]})

    # Thêm history
    for msg in history:
        messages.append({"role": msg["role"], "parts": [msg["content"]]})

    # Thêm câu hỏi mới
    messages.append({"role": "user", "parts": [question]})

    try:
        response = model.generate_content(messages)
        return response.text
    except Exception as e:
        return f"Lỗi khi gọi chatbot: {e}"

