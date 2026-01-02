# Chat Module - DaiHiep Sport

Module chatbot hoàn chỉnh với chat history đầy đủ.

## Tính năng

1. **Chat với AI**: Gửi câu hỏi và nhận câu trả lời từ FPT AI
2. **Chat History**: Tự động lưu và sử dụng lịch sử chat để trả lời chính xác
3. **Session Management**: Quản lý các phiên chat riêng biệt
4. **Booking History**: Tự động cung cấp lịch sử đặt sân cho chatbot

## API Endpoints

### 1. POST /api/chat/
Gửi câu hỏi đến chatbot

**Request:**
```json
{
  "q": "Tìm sân bóng đá tối nay",
  "session_id": "uuid-optional"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "question": "Tìm sân bóng đá tối nay",
  "answer": "Câu trả lời từ chatbot..."
}
```

### 2. GET /api/chat/history/?session_id=<uuid>
Lấy lịch sử chat của một session

**Response:**
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Xin chào",
      "created_at": "2025-01-01T10:00:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Xin chào! Tôi có thể giúp gì cho bạn?",
      "created_at": "2025-01-01T10:00:01Z"
    }
  ],
  "total": 2
}
```

### 3. GET /api/chat/sessions/
Lấy danh sách sessions của user

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "message_count": 10,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-01T11:00:00Z"
    }
  ],
  "total": 1
}
```

## Cấu trúc Module

```
apps/chat/
├── models.py              # ChatSession, ChatMessage
├── services.py            # Logic chatbot với chat history
├── admin.py               # Django admin
├── views.py               # View exports
├── urls.py                # URL routing
├── migrations/            # Database migrations
├── view_container/
│   ├── chatbot.py         # API chat chính
│   └── chat_history.py    # API lịch sử chat
└── README.md              # Tài liệu này
```

## Cách hoạt động

1. **Chat History Loading**: 
   - Khi user gửi câu hỏi, hệ thống tự động load lịch sử chat từ database (tối đa 20 messages gần nhất)
   - Lịch sử được thêm vào context để AI hiểu ngữ cảnh

2. **Session Management**:
   - Mỗi session có `session_id` (UUID) duy nhất
   - User có thể tiếp tục cuộc trò chuyện bằng cách dùng cùng `session_id`
   - Nếu không có `session_id`, hệ thống tạo session mới

3. **Booking History**:
   - Tự động load 10 booking gần nhất của user (nếu đã đăng nhập)
   - Cung cấp thông tin này cho AI để trả lời chính xác hơn

4. **Tránh vòng lặp**:
   - Câu hỏi hiện tại được lưu SAU KHI gọi API
   - Chat history chỉ load các messages đã lưu trước đó
   - Giới hạn 20 messages để tránh vượt quá token limit

## Database Models

### ChatSession
- `user`: ForeignKey to User (nullable)
- `session_id`: UUID (unique)
- `created_at`: DateTime
- `updated_at`: DateTime

### ChatMessage
- `session`: ForeignKey to ChatSession
- `role`: 'user' hoặc 'assistant'
- `content`: Text
- `created_at`: DateTime

## Rate Limiting

- Mặc định: 20 requests/phút/user
- Cấu hình trong `settings.CHAT_LIMIT_PER_MINUTE`

## Permissions

- Tất cả endpoints yêu cầu authentication (`IsUser`)
- User chỉ có thể truy cập sessions của chính mình

