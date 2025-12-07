# Context Backend - Sport DH

## Tổng quan
Backend của dự án Sport DH được xây dựng bằng Django REST Framework, phục vụ quản lý và đặt sân thể thao tại Đà Nẵng.

## Công nghệ sử dụng
- **Framework**: Django 5.2.4
- **API**: Django REST Framework 3.16.0
- **Authentication**: JWT (Simple JWT) với cookie-based authentication
- **Database**: SQLite3 (development)
- **Image Processing**: Pillow 11.3.0
- **AI Chatbot**: Google Generative AI 0.8.5
- **Package Manager**: Poetry

## Cấu trúc dự án

### Apps chính

#### 1. `apps/user/` - Quản lý người dùng
**Models:**
- `User`: Custom user model với UUID primary key
  - Fields: id (UUID), email, username, password, full_name, avatar, role, settings (JSON), is_active, address, phone, verify_code, device_tokens (JSON), is_delete, created_at, updated_at
  - Roles: ADMIN, OWNER, USER (RoleSystemEnum)
  - USERNAME_FIELD: username
  - Custom UserManager với create_user và create_superuser

- `ChatSession`: Quản lý session chatbot
  - Fields: user (FK), session_id (UUID), created_at

- `ChatMessage`: Lưu tin nhắn chatbot
  - Fields: session (FK), role (USER/BOT), content, created_at

**Views:**
- `RegisterViewSet`: Đăng ký user mới
- `VerifyCodeViewSet`: Xác thực email
- `UserDetailViewSet`: Lấy thông tin user hiện tại (`/user/me/`)
- `UserViewSet`: CRUD users (chỉ ADMIN)
- `ChatbotViewSet`: Xử lý chatbot với Google AI

**URLs:**
- `/api/auth/register/` - POST: Đăng ký
- `/api/auth/veryfi_code/` - POST: Xác thực code
- `/api/user/me/` - GET: Thông tin user hiện tại
- `/api/user/` - CRUD users
- `/api/chatbot/` - POST: Chat với AI

**Authentication:**
- Cookie-based JWT authentication (`CookieJWTAuthentication`)
- Access token và refresh token lưu trong HTTP-only cookies
- Endpoints: `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/logout/`, `/api/auth/verify/`

#### 2. `apps/sport_center/` - Quản lý trung tâm và sân thể thao
**Models:**
- `SportCenter`: Trung tâm thể thao
  - Fields: owner (FK User), name, address, created_at, updated_at
  - Quan hệ: 1-N với SportField

- `SportField`: Sân thể thao
  - Fields: sport_center (FK), name, address, sport_type (FOOTBALL/BADMINTON/TENNIS/PICK_A_BALL), price (Float), status (ACTIVE/INACTIVE), created_at, updated_at

- `ImageSport`: Quản lý ảnh (Generic Foreign Key)
  - Fields: file (ImageField), preview (ImageField - tự động tạo thumbnail), content_type, object_id
  - Hỗ trợ: SportCenter và SportField
  - Tự động tạo preview 700x700 với quality 70 khi upload

**Views:**
- `SportCenterViewSet`: CRUD sport centers
  - Filter: owner, name, address
  - Hỗ trợ upload nhiều ảnh qua FormData
  - Annotate total_field (số sân)

- `SportFieldViewSet`: CRUD sport fields
  - Filter: sport_center, status, center_name, sport_type, address, price_lte
  - Hỗ trợ upload nhiều ảnh

- `ImageSportDeleteViewSet`: Xóa ảnh

**URLs:**
- `/api/sport_center/` - CRUD sport centers
- `/api/sport_field/` - CRUD sport fields
- `/api/image_sport/<id>/delete/` - DELETE: Xóa ảnh

#### 3. `apps/booking/` - Quản lý đặt sân
**Models:**
- `RentalSlot`: Khung giờ cho thuê
  - Fields: name, time_slot (string), created_at, updated_at
  - Ví dụ: "06:00-07:00", "07:00-08:00"

- `Booking`: Đặt sân
  - Fields: user (FK, nullable), sport_field (FK), rental_slot (FK), price (Float), booking_date (Date), status (PENDING/CONFIRMED/COMPLETED/CANCELLED), created_at, updated_at

**Views:**
- `RentalSlotViewSet`: CRUD rental slots
- `BookingViewSet`: CRUD bookings (cho user)
  - Filter: sport_field, rental_slot, price, booking_date, booking_date_after, booking_date_before, month, year, status
  - Update status: PENDING ↔ CONFIRMED

- `BookingListTiniViewSet`: List bookings mini (chỉ rental_slot info)
- `BookingManageViewSet`: Quản lý bookings (admin/owner)
  - Owner: chỉ thấy bookings của sân thuộc về mình
  - User: chỉ thấy bookings của mình
  - Actions:
    - `bulk_create_day/`: Tạo bookings cho 1 ngày
    - `bulk_create_month/`: Tạo bookings cho 1 tháng

**URLs:**
- `/api/rental_slot/` - CRUD rental slots
- `/api/booking/` - CRUD bookings
- `/api/booking/list/` - GET: List bookings mini
- `/api/booking_manage/` - Quản lý bookings (admin/owner)

## Database Schema

### User
```
- id: UUID (PK)
- email: EmailField (unique)
- username: CharField (unique)
- password: CharField
- full_name: CharField
- avatar: ImageField
- role: CharField (ADMIN/OWNER/USER)
- settings: JSONField
- is_active: BooleanField
- address: CharField
- phone: CharField
- verify_code: CharField
- device_tokens: JSONField
- is_delete: BooleanField
- created_at, updated_at: DateTimeField
```

### SportCenter
```
- id: BigAutoField (PK)
- owner: ForeignKey(User)
- name: CharField
- address: CharField
- created_at, updated_at: DateTimeField
```

### SportField
```
- id: BigAutoField (PK)
- sport_center: ForeignKey(SportCenter)
- name: CharField
- address: CharField
- sport_type: CharField (FOOTBALL/BADMINTON/TENNIS/PICK_A_BALL)
- price: FloatField
- status: CharField (ACTIVE/INACTIVE)
- created_at, updated_at: DateTimeField
```

### Booking
```
- id: BigAutoField (PK)
- user: ForeignKey(User, nullable)
- sport_field: ForeignKey(SportField)
- rental_slot: ForeignKey(RentalSlot)
- price: FloatField
- booking_date: DateField
- status: CharField (PENDING/CONFIRMED/COMPLETED/CANCELLED)
- created_at, updated_at: DateTimeField
```

### RentalSlot
```
- id: BigAutoField (PK)
- name: CharField
- time_slot: CharField
- created_at, updated_at: DateTimeField
```

### ImageSport (Generic)
```
- id: BigAutoField (PK)
- file: ImageField
- preview: ImageField
- content_type: ForeignKey(ContentType)
- object_id: PositiveIntegerField
```

## Authentication & Authorization

### Authentication
- **Cookie-based JWT**: Tokens lưu trong HTTP-only cookies
- **Access Token**: Lifetime 3000 phút (mặc định)
- **Refresh Token**: Lifetime 7 ngày
- **Auto Refresh**: Tự động refresh khi access token sắp hết hạn

### Permissions
- `IsAdmin`: Chỉ ADMIN
- `IsOwner`: ADMIN hoặc OWNER
- `IsUser`: ADMIN, OWNER, hoặc USER

### Permission Rules
- **User CRUD**: Chỉ ADMIN
- **SportCenter CRUD**: IsUser (owner chỉ xóa được của mình)
- **SportField CRUD**: IsUser (owner chỉ xóa được của mình)
- **Booking**: IsUser (user chỉ thấy của mình, owner chỉ thấy của sân mình)

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Đăng nhập (trả về cookies)
- `POST /api/auth/register/` - Đăng ký
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Đăng xuất
- `POST /api/auth/verify/` - Verify token
- `POST /api/auth/veryfi_code/` - Xác thực email code

### User
- `GET /api/user/me/` - Thông tin user hiện tại
- `GET /api/user/` - List users (ADMIN)
- `POST /api/user/` - Tạo user (ADMIN)
- `GET /api/user/{id}/` - Chi tiết user (ADMIN)
- `PUT /api/user/{id}/` - Cập nhật user
- `DELETE /api/user/{id}/` - Xóa user (ADMIN)
- `PUT /api/user/update/settings/` - Cập nhật settings

### Sport Center
- `GET /api/sport_center/` - List centers (filter: owner, name, address)
- `POST /api/sport_center/` - Tạo center (FormData với images)
- `GET /api/sport_center/{id}/` - Chi tiết center
- `PUT /api/sport_center/{id}/` - Cập nhật center
- `DELETE /api/sport_center/{id}/` - Xóa center

### Sport Field
- `GET /api/sport_field/` - List fields (filter: sport_center, status, center_name, sport_type, address, price_lte)
- `POST /api/sport_field/` - Tạo field (FormData với images)
- `GET /api/sport_field/{id}/` - Chi tiết field
- `PUT /api/sport_field/{id}/` - Cập nhật field
- `DELETE /api/sport_field/{id}/` - Xóa field

### Booking
- `GET /api/booking/` - List bookings (filter: sport_field, rental_slot, booking_date, status, month, year)
- `GET /api/booking/list/` - List bookings mini
- `GET /api/booking/{id}/` - Chi tiết booking
- `PUT /api/booking/{id}/` - Cập nhật booking (status)
- `DELETE /api/booking/{id}/` - Xóa booking (ADMIN)

### Booking Manage (Admin/Owner)
- `GET /api/booking_manage/` - List bookings (filter theo role)
- `POST /api/booking_manage/bulk-create-day/` - Tạo bookings cho 1 ngày
- `POST /api/booking_manage/bulk-create-month/` - Tạo bookings cho 1 tháng

### Rental Slot
- `GET /api/rental_slot/` - List rental slots
- `POST /api/rental_slot/` - Tạo rental slot
- `GET /api/rental_slot/{id}/` - Chi tiết
- `PUT /api/rental_slot/{id}/` - Cập nhật
- `DELETE /api/rental_slot/{id}/` - Xóa

### Image
- `DELETE /api/image_sport/{id}/delete/` - Xóa ảnh

### Chatbot
- `POST /api/chatbot/?q={question}` - Chat với AI

## Settings

### CORS
- `CORS_ORIGIN_ALLOW_ALL = True`
- Allowed origins: localhost:3000, 3001, 5173, 5174, index-dh.daihiep.click
- `CORS_ALLOW_CREDENTIALS = True`

### Media & Static
- `MEDIA_URL = 'media/'`
- `MEDIA_ROOT = BASE_DIR / 'media'`
- `STATIC_URL = 'static/'`
- `STATIC_ROOT = BASE_DIR / 'static'`

### JWT Settings
- Access token lifetime: 3000 phút (env: ACCESS_TOKEN_LIFETIME)
- Refresh token lifetime: 7 ngày (env: REFRESH_TOKEN_LIFETIME)
- Cookie names: `access_token`, `refresh_token`
- Cookie settings: HttpOnly, SameSite=Lax

## Enums

### RoleSystemEnum
- `ADMIN`: Quản trị viên
- `OWNER`: Chủ sân
- `USER`: Người dùng

### StatusFieldEnum
- `ACTIVE`: Sân đang hoạt động
- `INACTIVE`: Sân không hoạt động

### StatusBookingEnum
- `PENDING`: Chờ xác nhận
- `CONFIRMED`: Đã xác nhận
- `COMPLETED`: Hoàn thành
- `CANCELLED`: Đã hủy

### SportTypeEnum
- `FOOTBALL`: Bóng đá
- `BADMINTON`: Cầu lông
- `TENNIS`: Tennis
- `PICK_A_BALL`: Pick a ball

## Utilities

### Image Processing
- Tự động tạo preview 700x700 với quality 70
- Hỗ trợ RGBA → RGB conversion
- Lưu preview trong `images/preview/`

### Mapping Data
- `MappingData`: Utility để map images với objects (sport centers/fields)

### Error Handling
- `AppStatus`: Enum cho các status codes và messages
- Validation errors trả về field-level errors

## Pagination
- `LimitOffsetPagination`: Sử dụng limit/offset
- Default: không giới hạn (có thể set limit/offset trong query params)

## Filtering
- Django Filter Backend
- Filter classes: `UserFilter`, `SportCenterFilter`, `SportFieldFilter`, `BookingFilter`, `BookingManageFilter`
- Ordering: hỗ trợ ordering_fields

## Logging
- Logs directory: `logs/`
- Files: `debug.log`, `error.log`
- Format: verbose với levelname, asctime, module, message

