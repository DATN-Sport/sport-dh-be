# Fake Data API

API endpoints để tạo fake data cho demo/báo cáo đồ án.

## Endpoints

### 1. Tạo Fake Users

**GET** `/api/fake_data/user/?count=20`

Tạo users với role USER.

**Query Parameters:**
- `count` (optional): Số lượng users cần tạo (mặc định: 20)

**Response:**
```json
{
  "message": "Created/Found 20 users",
  "count": 20,
  "users": [
    {
      "id": "uuid",
      "username": "user_01",
      "email": "user_01@gmail.com",
      "full_name": "Ngô Thị Nga",
      "status": "created" // hoặc "existed" nếu đã tồn tại
    }
  ]
}
```

**Format:**
- Username: `user_01`, `user_02`, ..., `user_20`
- Email: `user_01@gmail.com`, `user_02@gmail.com`, ...
- Password: `12345678` (cho tất cả)
- Role: `USER`
- is_active: `true`
- Full name: Random từ danh sách tên Việt Nam

### 2. Tạo Fake Bookings

**GET** `/api/fake_data/booking/?count=50`

Tạo bookings ngẫu nhiên từ users, sport_fields, và rental_slots có sẵn.

**Query Parameters:**
- `count` (optional): Số lượng bookings cần tạo (mặc định: 50)

**Yêu cầu:**
- Phải có ít nhất 1 user (role USER, is_active)
- Phải có ít nhất 1 sport_field (status ACTIVE)
- Phải có ít nhất 1 rental_slot

**Response:**
```json
{
  "message": "Created 50 bookings",
  "count": 50,
  "bookings": [
    {
      "id": 1,
      "user": "user_01",
      "sport_field": "Sân 7A",
      "booking_date": "2025-12-01",
      "status": "CONFIRMED",
      "price": 100000.0
    }
  ]
}
```

**Đặc điểm:**
- Booking date: Random trong 30 ngày gần đây
- Status: Random (CONFIRMED, COMPLETED, PENDING)
- Price: Copy từ sport_field.price

### 3. Tạo Booking Tự Động (Bulk Generate)

**GET** `/api/fake_data/booking/gen/`

Tạo booking từ tháng 6/2025 đến ngày hiện tại cho **TẤT CẢ** trung tâm và **TẤT CẢ** sân.

**Đặc điểm:**
- Tự động lặp qua tất cả sport_centers
- Tự động lặp qua tất cả tháng từ 6/2025 đến hiện tại
- Tự động lặp qua tất cả sport_fields (status ACTIVE)
- Tự động lặp qua tất cả rental_slots phù hợp với sport_type
- **Cho phép tạo booking trong quá khứ** (khác với bulk-create-month)
- Skip nếu booking đã tồn tại (sport_field + rental_slot + date)

**Response:**
```json
{
  "message": "Generated bookings from 6/2025 to 2025-12-08",
  "summary": {
    "total_created": 1500,
    "total_skipped": 200,
    "date_range": {
      "from": "6/2025",
      "to": "2025-12-08"
    }
  },
  "centers": [
    {
      "center_id": 1,
      "center_name": "DaiHiep Center 1",
      "created": 500,
      "skipped": 50
    }
  ]
}
```

### 4. Assign Users Vào Bookings

**GET** `/api/fake_data/booking/assign_users/`

Assign 40 users (user_01 đến user_40) vào bookings:
- **80% bookings từ 6/2025 đến hôm nay** → assign random cho 40 users, update status = CONFIRMED
- **40% bookings từ hôm nay đến 10/1/2026** → assign random cho 40 users, update status = CONFIRMED

**Response:**
```json
{
  "message": "Assigned users to bookings successfully",
  "summary": {
    "users_count": 40,
    "past_period": {
      "date_range": {
        "from": "2025-06-01",
        "to": "2025-12-07"
      },
      "total_bookings": 1000,
      "assigned": 800,
      "percent": 80
    },
    "future_period": {
      "date_range": {
        "from": "2025-12-08",
        "to": "2026-01-10"
      },
      "total_bookings": 500,
      "assigned": 200,
      "percent": 40
    },
    "total_assigned": 1000
  }
}
```

**Đặc điểm:**
- Chỉ assign vào bookings PENDING và chưa có user (user__isnull=True)
- Random assign cho 40 users
- Update status thành CONFIRMED (theo API PUT /api/booking/{id})
- Sử dụng bulk_update để tối ưu performance

### 5. Cập Nhật Booking Thành Success

**GET** `/api/fake_data/booking/success/?percent=30`

Cập nhật một số booking PENDING/CONFIRMED thành COMPLETED/CONFIRMED (successful bookings).

**Query Parameters:**
- `percent` (optional): Phần trăm booking cần update (0-100, mặc định: 30)

**Response:**
```json
{
  "message": "Updated 150 bookings to success status",
  "summary": {
    "total_updated": 150,
    "completed": 75,
    "confirmed": 75,
    "percent_applied": 30
  }
}
```

**Đặc điểm:**
- Chọn ngẫu nhiên từ bookings PENDING/CONFIRMED
- 50% update thành COMPLETED, 50% thành CONFIRMED
- Giúp có dữ liệu thống kê doanh thu (vì stats API chỉ tính CONFIRMED/COMPLETED)

## Cách sử dụng

1. **Tạo users:**
   ```bash
   curl http://localhost:8000/api/fake_data/user/?count=20
   ```

2. **Tạo bookings ngẫu nhiên:**
   ```bash
   curl http://localhost:8000/api/fake_data/booking/?count=50
   ```

3. **Tạo booking tự động (từ 6/2025 đến hiện tại):**
   ```bash
   curl http://localhost:8000/api/fake_data/booking/gen/
   ```

4. **Assign users vào bookings:**
   ```bash
   curl http://localhost:8000/api/fake_data/booking/assign_users/
   ```

5. **Cập nhật booking thành success:**
   ```bash
   curl http://localhost:8000/api/fake_data/booking/success/?percent=30
   ```

6. **Hoặc dùng browser/Postman:**
   - GET `http://localhost:8000/api/fake_data/user/?count=40`
   - GET `http://localhost:8000/api/fake_data/booking/gen/`
   - GET `http://localhost:8000/api/fake_data/booking/assign_users/`
   - GET `http://localhost:8000/api/fake_data/booking/success/?percent=30`

## Lưu ý

- Tất cả endpoints không yêu cầu authentication (AllowAny)
- Nếu user đã tồn tại (theo username), sẽ skip và trả về status "existed"
- `booking/gen/` tự động skip booking đã tồn tại (không tạo duplicate)
- `booking/gen/` có thể mất thời gian nếu có nhiều centers/fields/slots
- `booking/success/` chỉ update bookings PENDING/CONFIRMED, không update CANCELLED
- Response của `booking/` chỉ trả về 10 đầu tiên để tránh response quá dài

## Workflow đề xuất

1. Tạo users: `GET /api/fake_data/user/?count=40` (20 nữ + 20 nam)
2. Tạo booking tự động: `GET /api/fake_data/booking/gen/` (tạo từ 6/2025 đến hết 2/2026)
3. Assign users vào bookings: `GET /api/fake_data/booking/assign_users/` (80% past, 40% future)
4. Cập nhật một số booking thành success: `GET /api/fake_data/booking/success/?percent=30`
5. (Optional) Tạo thêm booking ngẫu nhiên: `GET /api/fake_data/booking/?count=50`
