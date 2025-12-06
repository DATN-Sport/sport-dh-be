# 📋 BOOKING API DOCUMENTATION

## 📌 Table of Contents
1. [RentalSlot APIs](#rentalslot-apis)
2. [Booking APIs](#booking-apis)
3. [Filtering & Ordering](#filtering--ordering)
4. [Error Handling](#error-handling)

---

## 🎯 RentalSlot APIs

Base URL: `/api/rental_slot/`

### 1. List RentalSlots
**Endpoint:** `GET /api/rental_slot/`

**Permission:** User (IsUser)

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Filter by name (case-insensitive) | `FOOTBALL`, `SPORT` |
| `time_slot` | string | Filter by time slot (case-insensitive) | `06:30 - 07:30` |
| `limit` | integer | Number of items per page | `10` |
| `offset` | integer | Pagination offset | `0` |
| `ordering` | string | Sort by field(s) | `name`, `-time_slot` |

**Available Ordering Fields:**
- `name`
- `time_slot`
- Use `-` prefix for descending order (e.g., `-name`)

**Response:**
```json
{
  "count": 30,
  "next": "http://api.example.com/api/rental_slot?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "FOOTBALL",
      "time_slot": "06:30 - 07:30",
      "created_at": "2025-09-26T07:52:00Z",
      "updated_at": "2025-09-26T07:52:00Z"
    }
  ]
}
```

---

### 2. Get RentalSlot Detail
**Endpoint:** `GET /api/rental_slot/{id}`

**Permission:** User (IsUser)

**Response:**
```json
{
  "id": 1,
  "name": "FOOTBALL",
  "time_slot": "06:30 - 07:30",
  "created_at": "2025-09-26T07:52:00Z",
  "updated_at": "2025-09-26T07:52:00Z",
  "images": []
}
```

---

### 3. Create RentalSlot
**Endpoint:** `POST /api/rental_slot/`

**Permission:** Admin only

**Request Body:**
```json
{
  "name": "FOOTBALL",
  "time_slot": "06:30 - 07:30"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "FOOTBALL",
  "time_slot": "06:30 - 07:30"
}
```

**Error Cases:**
- Non-admin user: `403 Forbidden` - "PERMISSION_DENIED"

---

### 4. Update RentalSlot
**Endpoint:** `PUT/PATCH /api/rental_slot/{id}`

**Permission:** Admin only

**Request Body:**
```json
{
  "name": "SPORT",
  "time_slot": "08:00 - 09:00"
}
```

**Response:**
```json
{
  "detail": "Update RentalSlot successfully"
}
```

---

### 5. Delete RentalSlot
**Endpoint:** `DELETE /api/rental_slot/{id}`

**Permission:** Admin only

**Response:**
```json
{
  "detail": "Time slot deleted successfully"
}
```

---

## 🏟️ Booking APIs

Base URL: `/api/booking/`

### 1. List Bookings (Full Detail)
**Endpoint:** `GET /api/booking/`

**Permission:** User (IsUser)

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `sport_field` | integer | Filter by sport field ID | `1` |
| `rental_slot` | integer | Filter by rental slot ID | `2` |
| `price` | number | Filter by exact price | `100000` |
| `booking_date` | date | Filter by exact date | `2025-10-20` |
| `booking_date_after` | date | Filter from date (>=) | `2025-10-01` |
| `booking_date_before` | date | Filter to date (<=) | `2025-10-31` |
| `month` | integer | Filter by month (1-12) | `10` |
| `year` | integer | Filter by year | `2025` |
| `status` | string | Filter by status | `PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED` |
| `limit` | integer | Items per page | `10` |
| `offset` | integer | Pagination offset | `0` |
| `ordering` | string | Sort by field(s) | `booking_date`, `-created_at` |

**Available Ordering Fields:**
- `price`
- `booking_date`
- `status`
- `created_at`

**Default Ordering:** `booking_date` (ascending)

**Response:**
```json
{
  "count": 100,
  "next": "http://api.example.com/api/booking/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 5,
        "full_name": "Nguyen Van A",
        "email": "user@example.com",
        "phone": "0123456789"
      },
      "sport_field": {
        "id": 3,
        "name": "San Bong 1",
        "sport_type": "FOOTBALL",
        "address": "123 Nguyen Van Linh, Da Nang"
      },
      "rental_slot": {
        "id": 2,
        "name": "FOOTBALL",
        "time_slot": "06:30 - 07:30"
      },
      "status": "CONFIRMED",
      "price": 200000,
      "booking_date": "2025-10-20"
    }
  ]
}
```

---

### 2. List Bookings (Mini Version)
**Endpoint:** `GET /api/booking/list/`

**Permission:** User (IsUser)

**Query Parameters:** Same as full booking list

**Response:**
```json
{
  "count": 100,
  "next": "http://api.example.com/api/booking/list/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "sport_field": 3,
      "rental_slot": "06:30 - 07:30",
      "status": "CONFIRMED",
      "booking_date": "2025-10-20"
    }
  ]
}
```

**Use Case:** Sử dụng khi cần list nhanh, ít data hơn để hiển thị calendar hoặc danh sách đơn giản.

---

### 3. Get Booking Detail
**Endpoint:** `GET /api/booking/{id}`

**Permission:** User (IsUser)

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 5,
    "full_name": "Nguyen Van A",
    "email": "user@example.com",
    "phone": "0123456789"
  },
  "sport_field": {
    "id": 3,
    "name": "San Bong 1",
    "sport_type": "FOOTBALL",
    "address": "123 Nguyen Van Linh, Da Nang"
  },
  "rental_slot": {
    "id": 2,
    "name": "FOOTBALL",
    "time_slot": "06:30 - 07:30"
  },
  "status": "CONFIRMED",
  "price": 200000,
  "booking_date": "2025-10-20"
}
```

---

### 4. Create Single Booking
**Endpoint:** `POST /api/booking/`

**Permission:** Admin only

**Request Body:**
```json
{
  "user": 5,
  "sport_field": 3,
  "rental_slot": 2,
  "booking_date": "2025-10-20",
  "status": "PENDING"
}
```

**Fields:**
- `sport_field` - **Required** (integer)
- `rental_slot` - **Required** (integer)
- `user` - Optional (integer), có thể null
- `booking_date` - Optional (date), nếu không truyền sẽ dùng ngày hiện tại
- `status` - Optional (string), default là `PENDING`

**Response:**
```json
{
  "id": 1,
  "user": {...},
  "sport_field": {...},
  "rental_slot": {...},
  "status": "PENDING",
  "price": 200000,
  "booking_date": "2025-10-20"
}
```

**Notes:**
- `price` sẽ tự động lấy từ `sport_field.price`
- Chỉ admin mới có quyền tạo booking

---

### 5. Bulk Create Bookings (By Day)
**Endpoint:** `POST /api/booking/bulk-create-day/`

**Permission:** Admin only

**Request Body:**
```json
{
  "sport_center": 1,
  "booking_date": "2025-10-20"
}
```

**Fields:**
- `sport_center` - **Required** (integer)
- `booking_date` - **Required** (date)

**Response:**
```json
{
  "message": "Bookings created successfully",
  "data": {
    "created_count": 48,
    "skipped_count": 12,
    "total_slots": 60,
    "booking_date": "2025-10-20",
    "sport_center": {
      "id": 1,
      "name": "Sport Center ABC"
    }
  }
}
```

**Logic:**
1. Tìm tất cả sport fields thuộc sport_center với status = `ACTIVE`
2. Lấy các rental slots phù hợp với sport_type của từng field
3. Tạo booking cho tất cả combinations (field × slot) trong ngày
4. Skip nếu booking đã tồn tại (same field, slot, date)

**Error Cases:**
- No active fields: `"NO_ACTIVE_SPORT_FIELDS_FOUND"`
- No rental slots: Không có slots phù hợp với sport_type

---

### 6. Bulk Create Bookings (By Month)
**Endpoint:** `POST /api/booking/bulk-create-month/`

**Permission:** Admin only

**Request Body:**
```json
{
  "sport_center": 1,
  "month": 10,
  "year": 2025
}
```

**Fields:**
- `sport_center` - **Required** (integer)
- `month` - **Required** (integer, 1-12)
- `year` - **Required** (integer, >= 2025)

**Response:**
```json
{
  "message": "Bookings created successfully for 15 days",
  "data": {
    "created_count": 720,
    "skipped_count": 180,
    "total_slots": 900,
    "month": 10,
    "year": 2025,
    "num_days": 15,
    "sport_center": {
      "id": 1,
      "name": "Sport Center ABC"
    }
  }
}
```

**Logic:**
1. Tính số ngày trong tháng
2. **Chỉ tạo booking từ ngày hiện tại trở đi** (không tạo cho ngày quá khứ)
3. Tạo booking cho tất cả combinations (field × slot × date)
4. Batch create 1000 records một lần để tối ưu performance

**Validation Rules:**
- Month phải từ 1-12
- Year phải >= 2025
- Không cho phép tạo booking cho tháng đã qua

**Error Cases:**
- Invalid month/year: `"Invalid month/year combination"`
- Past month: `"Cannot create bookings for past months"`
- No valid dates: `"NO_VALID_DATES_IN_THIS_MONTH"`
- No active fields: `"NO_ACTIVE_SPORT_FIELDS_FOUND"`
- No rental slots: `"NO_RENTAL_SLOTS_FOUND"`

---

### 7. Update Booking
**Endpoint:** `PUT/PATCH /api/booking/{id}`

**Permission:** User (IsUser)

**Request Body:**
```json
{
  "user": 5,
  "status": "CONFIRMED"
}
```

**Fields:**
- `user` - Optional (integer)
- `status` - **Required** (string)

**Update Rules:**

#### 🔐 Admin User:
- Có thể update bất kỳ field nào
- Có thể assign user vào booking

#### 👤 Normal User:

**Scenario 1: Đặt sân (PENDING → CONFIRMED)**
```json
{
  "status": "CONFIRMED"
}
```
- Booking phải đang ở trạng thái `PENDING`
- Chuyển sang `CONFIRMED` và gán `user = current_user`

**Scenario 2: Hủy đặt (CONFIRMED → PENDING)**
```json
{
  "status": "PENDING"
}
```
- Booking phải đang ở trạng thái `CONFIRMED`
- Chuyển về `PENDING` và set `user = null`

**Scenario 3: Các trường hợp khác**
- Không được phép update
- Trả về lỗi: `"PERMISSION_DENIED"`

**Response:**
```json
{
  "id": 1,
  "user": {...},
  "sport_field": {...},
  "rental_slot": {...},
  "status": "CONFIRMED",
  "price": 200000,
  "booking_date": "2025-10-20"
}
```

**Error Cases:**
- User tries to assign another user: `"PERMISSION_DENIED"`
- Invalid status transition: `"PERMISSION_DENIED"`
- Non-admin tries admin actions: `"PERMISSION_DENIED"`

---

### 8. Delete Booking
**Endpoint:** `DELETE /api/booking/{id}`

**Permission:** Admin only

**Response:**
```json
{
  "detail": "Time slot deleted successfully"
}
```

---

## 🔍 Filtering & Ordering

### Date Filtering Examples

#### Filter by exact date:
```
GET /api/booking/?booking_date_=2025-10-20
```

#### Filter by date range:
```
GET /api/booking/?booking_date_after=2025-10-01&booking_date_before=2025-10-31
```

#### Filter by month and year:
```
GET /api/booking/?month=10&year=2025
```

#### Filter by month only:
```
GET /api/booking/?month=10
```

#### Filter by year only:
```
GET /api/booking/?year=2025
```

---

### Status Filtering

**Available Statuses:**
- `PENDING` - Chưa được đặt
- `CONFIRMED` - Đã được đặt
- `COMPLETED` - Đã hoàn thành
- `CANCELLED` - Đã hủy

**Example:**
```
GET /api/booking/?status=PENDING
GET /api/booking/?status=CONFIRMED
```

---

### Multiple Filters

Combine multiple filters:
```
GET /api/booking/?sport_field=3&month=10&year=2025&status=CONFIRMED
```

---

### Ordering Examples

#### Single field ascending:
```
GET /api/booking/?ordering=booking_date
```

#### Single field descending:
```
GET /api/booking/?ordering=-booking_date
```

#### Multiple fields:
```
GET /api/booking/?ordering=booking_date,-created_at
```

**Note:** Separate multiple fields with comma, no space

---

### Pagination

**Using limit & offset:**
```
GET /api/booking/?limit=20&offset=0   # Page 1
GET /api/booking/?limit=20&offset=20  # Page 2
GET /api/booking/?limit=20&offset=40  # Page 3
```

**Default Limit:** Check your backend settings (usually 10-20)

---

## ⚠️ Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "sport_field": ["This field is required."],
  "rental_slot": ["This field is required."]
}
```

#### 403 Forbidden
```json
{
  "detail": "PERMISSION_DENIED"
}
```

#### 404 Not Found
```json
{
  "detail": "Not found."
}
```

#### Validation Errors
```json
{
  "month": ["Month must be between 1 and 12."],
  "year": ["Year must be at least 2025."]
}
```

---

## 📝 Usage Examples

### Example 1: Get available slots for a date
```javascript
// Get all PENDING bookings for a specific field and date
const response = await fetch(
  '/api/booking/list/?sport_field=3&booking_date_=2025-10-20&status=PENDING'
);
const data = await response.json();
```

### Example 2: User books a slot
```javascript
// User clicks on a PENDING slot to book
const response = await fetch('/api/booking/5', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    status: 'CONFIRMED'
  })
});
```

### Example 3: Admin creates bookings for entire month
```javascript
const response = await fetch('/api/booking/bulk-create-month/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ADMIN_TOKEN'
  },
  body: JSON.stringify({
    sport_center: 1,
    month: 11,
    year: 2025
  })
});
```

### Example 4: Get bookings for calendar view
```javascript
// Get all bookings for a month to display on calendar
const response = await fetch(
  '/api/booking/list/?month=10&year=2025&ordering=booking_date'
);
const data = await response.json();
```

---

## 🎨 UI Implementation Suggestions

### Calendar View
1. Use `/api/booking/list/` với filter `month` và `year`
2. Group bookings by `booking_date`
3. Color code by `status`:
   - PENDING: Xanh lá (available)
   - CONFIRMED: Xám (booked)
   - COMPLETED: Xanh dương
   - CANCELLED: Đỏ

### Booking Process
1. User selects date → Fetch PENDING slots
2. User selects slot → Call PATCH with `status: CONFIRMED`
3. Show confirmation message
4. Refresh booking list

### Admin Dashboard
1. Use bulk create for quick setup
2. Monitor `created_count` vs `skipped_count`
3. Show statistics by status

---

## 📌 Important Notes

1. **Timezone:** All dates are in UTC. Convert to local timezone on frontend if needed.

2. **Performance:** 
   - Use `/api/booking/list/` for calendar views (lighter payload)
   - Use `/api/booking/` for detail pages

3. **Caching:** Consider caching booking lists on frontend and refresh on user actions.

4. **Real-time:** Consider implementing WebSocket for real-time booking updates if multiple users book simultaneously.

5. **Default Data:** RentalSlots are auto-generated on app startup:
   - FOOTBALL: 06:30 - 22:30 (1-hour slots)
   - SPORT: 08:00 - 20:00 (1-hour slots)

---

## 🔗 Quick Reference

| Action | Endpoint                          | Method | Permission |
|--------|-----------------------------------|--------|------------|
| List Bookings | `/api/booking/`                   | GET | User |
| List Mini | `/api/booking/list/`              | GET | User |
| Get Detail | `/api/booking/{id}`               | GET | User |
| Create Single | `/api/booking/`                   | POST | Admin |
| Bulk Day | `/api/booking/bulk-create-day/`   | POST | Admin |
| Bulk Month | `/api/booking/bulk-create-month/` | POST | Admin |
| Update | `/api/booking/{id}`               | PATCH | User |
| Delete | `/api/booking/{id}`               | DELETE | Admin |

---

**Last Updated:** October 17, 2025  
**Version:** 1.0  
**Contact:** [Your Support Email]