# Phân tích dự án Sport DH Backend

## 1. Tổng quan

**Tên dự án**: DaiHiep Sport - Nền tảng đặt sân thể thao trực tuyến  
**Framework**: Django 5.2.5 + Django REST Framework  
**Database**: SQLite3 (development)  
**Authentication**: JWT (Cookie-based + Header fallback)  
**Documentation**: Swagger/OpenAPI (drf-yasg)  
**Timezone**: Asia/Ho_Chi_Minh

## 2. Cấu trúc dự án

```
sport-dh-be/
├── apps/
│   ├── user/              # Quản lý người dùng, authentication, chatbot
│   ├── sport_center/      # Quản lý trung tâm thể thao và sân
│   ├── booking/           # Quản lý đặt sân, rental slots, thống kê
│   ├── depends/           # Authentication dependencies
│   └── utils/             # Utilities chung (chatbot, enum, constants)
├── sport_dh/              # Django project settings
└── manage.py
```

## 3. Models & Database Schema

### 3.1 User App

**User** (Custom AbstractBaseUser):
- `id`: UUID (primary key)
- `email`, `username`: unique
- `full_name`, `avatar`, `address`, `phone`
- `role`: ADMIN | OWNER | USER
- `is_active`, `is_superuser`, `is_delete`
- `settings`: JSONField
- `device_tokens`: JSONField (push notifications)
- `verify_code`: email verification

**ChatSession**:
- `user`: ForeignKey (nullable)
- `session_id`: UUID (unique)
- `created_at`

**ChatMessage**:
- `session`: ForeignKey → ChatSession
- `role`: USER | BOT
- `content`: TextField
- `created_at`

### 3.2 Sport Center App

**SportCenter**:
- `owner`: ForeignKey → User
- `name`, `address`
- `created_at`, `updated_at`

**SportField**:
- `sport_center`: ForeignKey → SportCenter
- `name`, `address`
- `sport_type`: FOOTBALL | BADMINTON | TENNIS | PICK_A_BALL
- `price`: FloatField
- `status`: ACTIVE | INACTIVE
- `created_at`, `updated_at`

**ImageSport** (GenericForeignKey):
- `file`: ImageField
- `preview`: ImageField (auto-generated thumbnail)
- `content_type`, `object_id`: Generic relation
- Hỗ trợ attach images cho SportCenter hoặc SportField

### 3.3 Booking App

**RentalSlot**:
- `name`: CharField (thường là sport_type)
- `time_slot`: CharField (format: "07:00-08:00")
- `created_at`, `updated_at`

**Booking**:
- `user`: ForeignKey → User (nullable)
- `sport_field`: ForeignKey → SportField
- `rental_slot`: ForeignKey → RentalSlot
- `price`: FloatField (copy từ sport_field.price khi tạo)
- `booking_date`: DateField
- `status`: PENDING | CONFIRMED | COMPLETED | CANCELLED
- `created_at`, `updated_at`

## 4. Authentication & Authorization

### 4.1 Authentication Flow

**Cookie-based JWT** (primary):
- Login: `POST /api/auth/login/` → set cookies `access_token`, `refresh_token` (HTTP-only)
- Refresh: `POST /api/auth/refresh/` → renew access token
- Logout: `POST /api/auth/logout/` → clear cookies
- Fallback: Header `Authorization: Bearer <token>` (cho API clients)

**Custom Token Serializers**:
- `CustomTokenObtainPairSerializer`: trả user info + message
- `CustomTokenRefreshSerializer`: refresh với cookie

### 4.2 Permission Classes

**IsUser**: Cho phép USER, OWNER, ADMIN  
**IsOwner**: Cho phép OWNER, ADMIN  
**IsAdmin**: Chỉ ADMIN

### 4.3 Role-based Access Control

- **ADMIN**: Full access, quản lý tất cả dữ liệu
- **OWNER**: Quản lý sport_center của mình, xem booking của center mình
- **USER**: Xem/đặt booking, xem thông tin công khai

## 5. API Endpoints

### 5.1 User APIs (`/api/`)

- `POST /api/auth/register/` - Đăng ký
- `POST /api/auth/veryfi_code/` - Xác thực email
- `POST /api/auth/login/` - Đăng nhập (cookie JWT)
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Đăng xuất
- `GET /api/user/me/` - Thông tin user hiện tại
- `GET /api/user/` - List users (ADMIN only)
- `GET /api/user/{id}/` - Chi tiết user (ADMIN only)
- `POST /api/chatbot/` - Chat với AI bot (rate-limited)

### 5.2 Sport Center APIs (`/api/`)

- `GET /api/sport_center/` - List centers (filter: owner, name, address)
- `POST /api/sport_center/` - Tạo center (ADMIN only, có thể upload images)
- `GET /api/sport_center/{id}/` - Chi tiết center (kèm images)
- `PUT /api/sport_center/{id}/` - Update center (owner hoặc ADMIN)
- `DELETE /api/sport_center/{id}/` - Xóa center

- `GET /api/sport_field/` - List fields (filter: sport_center, sport_type, price, status)
- `POST /api/sport_field/` - Tạo field (có thể upload images)
- `GET /api/sport_field/{id}/` - Chi tiết field (kèm images)
- `PUT /api/sport_field/{id}/` - Update field
- `DELETE /api/sport_field/{id}/` - Xóa field

- `DELETE /api/image_sport/{id}/delete/` - Xóa image

### 5.3 Booking APIs (`/api/`)

- `GET /api/rental_slot/` - List rental slots (filter: name, time_slot)
- `POST /api/rental_slot/` - Tạo slot
- `GET /api/rental_slot/{id}/` - Chi tiết slot
- `PUT /api/rental_slot/{id}/` - Update slot
- `DELETE /api/rental_slot/{id}/` - Xóa slot

- `GET /api/booking/` - List bookings (filter: user, sport_field, date, status)
- `POST /api/booking/` - Tạo booking (ADMIN only)
- `GET /api/booking/{id}/` - Chi tiết booking
- `PUT /api/booking/{id}/` - Update booking (status, user)
- `DELETE /api/booking/{id}/` - Xóa booking (ADMIN only)

- `GET /api/booking/list/` - List bookings (tini version, ít fields)

- `GET /api/booking_manage/` - List bookings với scope:
  - OWNER: chỉ center của mình
  - USER: chỉ booking của mình
  - ADMIN: tất cả
- `POST /api/booking_manage/bulk-create-day/` - Tạo booking hàng loạt cho 1 ngày
- `POST /api/booking_manage/bulk-create-month/` - Tạo booking hàng loạt cho 1 tháng

- `GET /api/booking/stats/` - **Thống kê doanh thu/booking** (OWNER/ADMIN)
  - Query params: `preset`, `date_from`, `date_to`, `statuses[]`, `limit_top_fields`
  - Response: summary, by_status, by_center, top_fields

## 6. Patterns & Conventions

### 6.1 View Structure

- **ViewSet** (ModelViewSet): CRUD operations với pagination, filtering, ordering
- **APIView**: Custom endpoints (stats, chatbot, bulk actions)
- **FilterSet**: Django-filter cho query params
- **Serializer**: Validation, nested data, custom methods

### 6.2 Serializer Patterns

- `DetailSerializer`: Full data cho retrieve/list
- `Serializer`: Minimal fields cho create/update
- `SerializerMethodField`: Custom computed fields
- Context: `image_map` cho images, `request.user` cho permissions

### 6.3 Filter Patterns

- Default filters: `BookingFilter` tự set `booking_date_=today` nếu không có filter
- Owner scope: `BookingManageFilter` tự filter theo owner nếu user là OWNER
- Date range: `DateFromToRangeFilter` cho khoảng ngày

### 6.4 Pagination

- `LimitOffsetPagination`: Standard cho tất cả list endpoints
- Config trong settings hoặc per-viewset

## 7. Features đặc biệt

### 7.1 Image Upload & Preview

- Upload multiple images qua `multipart/form-data`
- Auto-generate preview (thumbnail 700x700, JPEG, quality 70)
- GenericForeignKey: images có thể attach vào SportCenter hoặc SportField
- Delete images: xóa cả file và preview khi xóa object

### 7.2 Bulk Booking Creation

- **bulk-create-day**: Tạo booking cho tất cả sân + slots của 1 center trong 1 ngày
- **bulk-create-month**: Tạo booking cho cả tháng (chỉ từ ngày hiện tại trở đi)
- Logic: skip nếu booking đã tồn tại (sport_field + rental_slot + date)

### 7.3 Chatbot Integration

- **FPT AI API**: Sử dụng OpenAI client với FPT endpoint
- **Intent Detection**: Phân loại câu hỏi (availability_search, booking_history, pricing, etc.)
- **Parameter Extraction**: Tự động detect sport_type, date, time_slot, area từ text
- **Two-stage**: Analyze (hỏi thêm thông tin) → Final (trả lời với data)
- **Rate Limiting**: `CHAT_LIMIT_PER_MINUTE` (default 20)
- **Session Management**: ChatSession + ChatMessage lưu lịch sử

### 7.4 Statistics API

- **Date Presets**: today, this_week, this_month, this_quarter
- **Custom Date Range**: date_from/date_to
- **Status Filtering**: Mặc định CONFIRMED + COMPLETED
- **Owner Scope**: OWNER chỉ thấy center của mình
- **Aggregations**: total_revenue, total_bookings, by_status, by_center, top_fields

## 8. Utils & Helpers

### 8.1 Enum Types (`apps/utils/enum_type.py`)

- `RoleSystemEnum`: ADMIN, OWNER, USER
- `RoleChatEnum`: USER, BOT
- `StatusBookingEnum`: PENDING, CONFIRMED, COMPLETED, CANCELLED
- `StatusFieldEnum`: ACTIVE, INACTIVE
- `SportTypeEnum`: FOOTBALL, BADMINTON, TENNIS, PICK_A_BALL
- `TypeEmailEnum`: REGISTER, RESET_PASSWORD

### 8.2 Constants (`apps/utils/constant_status.py`)

- `AppStatus`: Enum với message và HTTP code
- Format: `(code, status_code, message)`
- Property `message`: trả dict với `message`, `code`, `data`

### 8.3 Cookie Utils (`apps/utils/cookie_utils.py`)

- `set_jwt_cookies()`: Set access + refresh tokens
- `clear_jwt_cookies()`: Clear tokens khi logout

### 8.4 Mapping Data (`apps/utils/mapping_data.py`)

- `MappingData.mapping_img()`: Map images theo object_id cho list views

## 9. Settings Highlights

### 9.1 JWT Configuration

```python
JWT_ACCESS_TOKEN_COOKIE = 'access_token'
JWT_REFRESH_TOKEN_COOKIE = 'refresh_token'
JWT_COOKIE_SECURE = False  # True in production
JWT_COOKIE_HTTPONLY = True
JWT_COOKIE_SAMESITE = 'Lax'
ACCESS_TOKEN_LIFETIME = 3000 minutes (default)
REFRESH_TOKEN_LIFETIME = 7 days (default)
```

### 9.2 CORS

- `CORS_ORIGIN_ALLOW_ALL = True` (dev)
- Allowed origins: localhost:3000, 3001, 5173, 5174, index-dh.daihiep.click
- Credentials: True

### 9.3 FPT AI

- `FPT_API_KEY`, `FPT_URL_API`, `FPT_MODEL_NAME`: từ env
- `CHAT_LIMIT_PER_MINUTE`: 20 (default)

## 10. Testing

- Test files: `apps/*/tests.py`
- Booking stats tests: Unit tests cho helper + API integration tests
- Test patterns: `_seed_data()` helper, `APITestCase` cho API tests

## 11. Migration Notes

- Custom User model: `AUTH_USER_MODEL = "user.User"`
- UUID primary key cho User
- GenericForeignKey cho ImageSport
- ForeignKey relationships: User → SportCenter → SportField → Booking

## 12. API Documentation

- Swagger UI: `/docs/`
- ReDoc: `/redoc/`
- YAML: `/swagger.yaml`
- Auto-generated từ drf-yasg với custom schemas

## 13. Code Style

- Vietnamese comments và user-facing messages
- Serializer methods: `get_<field>()` cho SerializerMethodField
- View methods: `get_queryset()`, `get_serializer_class()`, `get_object()`
- Error handling: `AppStatus` enum với consistent format
- Helper functions: prefix `_` cho private helpers

## 14. Dependencies

- **Core**: Django 5.2.5, djangorestframework, djangorestframework-simplejwt
- **Docs**: drf-yasg
- **Filtering**: django-filter
- **CORS**: django-cors-headers
- **Rate Limiting**: django-ratelimit
- **Images**: Pillow
- **AI**: openai (FPT API client)
- **Database**: psycopg2-binary (PostgreSQL support)

## 15. Environment Variables

- `SECRET_KEY`
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`
- `FPT_API_KEY`, `FPT_URL_API`, `FPT_MODEL_NAME`
- `CHAT_LIMIT_PER_MINUTE`
- `ACCESS_TOKEN_LIFETIME`, `REFRESH_TOKEN_LIFETIME`
- `CSRF_COOKIE_SECURE`, `JWT_COOKIE_SECURE`, `JWT_COOKIE_DOMAIN`

---

**Tài liệu này được tạo tự động dựa trên phân tích codebase. Cập nhật: 2025-12-08**

