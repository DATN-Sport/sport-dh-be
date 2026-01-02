-- Script chuyển đổi các cột UUID từ text sang UUID trong PostgreSQL
-- Chạy các lệnh này sau khi đã import dữ liệu từ SQLite sang PostgreSQL
-- 
-- CÁCH SỬ DỤNG:
-- psql -U postgres -d mydb -f convert_uuid_text_to_uuid.sql
-- hoặc
-- psql postgresql://postgres:postgres@localhost:5432/mydb -f convert_uuid_text_to_uuid.sql

-- Bước 1: Tạo hàm helper để format UUID string (thêm dấu gạch ngang nếu thiếu)
-- Hàm này sẽ chuyển đổi UUID không có dấu gạch ngang thành UUID có dấu gạch ngang
-- Ví dụ: "46afc70c54c343b3933ec00d18de30ba" -> "46afc70c-54c3-43b3-933e-c00d18de30ba"
CREATE OR REPLACE FUNCTION format_uuid_string(uuid_text TEXT)
RETURNS TEXT AS $$
DECLARE
    uuid_lower TEXT;
BEGIN
    -- Chuyển về chữ thường để xử lý
    uuid_lower := LOWER(TRIM(uuid_text));
    
    -- Nếu NULL hoặc rỗng, trả về NULL
    IF uuid_lower IS NULL OR uuid_lower = '' THEN
        RETURN NULL;
    END IF;
    
    -- Nếu đã có dấu gạch ngang, trả về chữ thường
    IF uuid_lower ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
        RETURN uuid_lower;
    END IF;
    
    -- Nếu không có dấu gạch ngang (32 ký tự hex), thêm vào đúng vị trí (8-4-4-4-12)
    IF uuid_lower ~ '^[0-9a-f]{32}$' THEN
        RETURN substring(uuid_lower, 1, 8) || '-' ||
               substring(uuid_lower, 9, 4) || '-' ||
               substring(uuid_lower, 13, 4) || '-' ||
               substring(uuid_lower, 17, 4) || '-' ||
               substring(uuid_lower, 21, 12);
    END IF;
    
    -- Nếu không phải format hợp lệ, trả về NULL để báo lỗi
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Bước 2: Chuyển đổi các cột UUID chính
BEGIN;

-- Tạm thời disable foreign key constraints
-- Lấy danh sách tất cả constraints và drop chúng
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop foreign key constraints liên quan đến user_user.id
    FOR r IN (
        SELECT conname, conrelid::regclass AS table_name
        FROM pg_constraint
        WHERE confrelid = 'user_user'::regclass
        AND contype = 'f'
    ) LOOP
        EXECUTE format('ALTER TABLE %s DROP CONSTRAINT IF EXISTS %s', r.table_name, r.conname);
        RAISE NOTICE 'Dropped constraint: % on table %', r.conname, r.table_name;
    END LOOP;
END $$;

-- Chuyển đổi user_user.id từ text sang UUID (Primary Key)
-- Sử dụng hàm format_uuid_string để thêm dấu gạch ngang nếu thiếu
ALTER TABLE user_user 
ALTER COLUMN id TYPE UUID USING format_uuid_string(id)::UUID;

-- Chuyển đổi user_chatsession.session_id từ text sang UUID
ALTER TABLE user_chatsession 
ALTER COLUMN session_id TYPE UUID USING format_uuid_string(session_id)::UUID;

-- Chuyển đổi các ForeignKey columns tham chiếu đến User.id

-- booking_booking.user_id
ALTER TABLE booking_booking 
ALTER COLUMN user_id TYPE UUID USING 
    CASE 
        WHEN user_id IS NULL OR user_id = '' THEN NULL
        ELSE format_uuid_string(user_id)::UUID
    END;

-- sport_center_sportcenter.owner_id
ALTER TABLE sport_center_sportcenter 
ALTER COLUMN owner_id TYPE UUID USING format_uuid_string(owner_id)::UUID;

-- user_chatsession.user_id (có thể NULL)
ALTER TABLE user_chatsession 
ALTER COLUMN user_id TYPE UUID USING 
    CASE 
        WHEN user_id IS NULL OR user_id = '' THEN NULL
        ELSE format_uuid_string(user_id)::UUID
    END;

-- user_user_groups.user_id (nếu bảng tồn tại)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_user_groups') THEN
        ALTER TABLE user_user_groups 
        ALTER COLUMN user_id TYPE UUID USING format_uuid_string(user_id)::UUID;
        RAISE NOTICE 'Converted user_user_groups.user_id';
    END IF;
END $$;

-- user_user_user_permissions.user_id (nếu bảng tồn tại)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_user_user_permissions') THEN
        ALTER TABLE user_user_user_permissions 
        ALTER COLUMN user_id TYPE UUID USING format_uuid_string(user_id)::UUID;
        RAISE NOTICE 'Converted user_user_user_permissions.user_id';
    END IF;
END $$;

-- Tạo lại foreign key constraints
ALTER TABLE booking_booking 
ADD CONSTRAINT booking_booking_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES user_user(id) ON DELETE CASCADE;

ALTER TABLE sport_center_sportcenter 
ADD CONSTRAINT sport_center_sportcenter_owner_id_fkey 
FOREIGN KEY (owner_id) REFERENCES user_user(id) ON DELETE CASCADE;

ALTER TABLE user_chatsession 
ADD CONSTRAINT user_chatsession_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES user_user(id) ON DELETE SET NULL;

-- Tạo lại constraints cho many-to-many tables (nếu có)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_user_groups') THEN
        ALTER TABLE user_user_groups 
        ADD CONSTRAINT user_user_groups_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES user_user(id) ON DELETE CASCADE;
        RAISE NOTICE 'Recreated constraint for user_user_groups';
    END IF;
END $$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_user_user_permissions') THEN
        ALTER TABLE user_user_user_permissions 
        ADD CONSTRAINT user_user_user_permissions_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES user_user(id) ON DELETE CASCADE;
        RAISE NOTICE 'Recreated constraint for user_user_user_permissions';
    END IF;
END $$;

COMMIT;

-- Xóa hàm helper sau khi sử dụng xong (tùy chọn)
DROP FUNCTION IF EXISTS format_uuid_string(TEXT);

-- Bước 3: Kiểm tra kết quả
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('user_user', 'user_chatsession', 'booking_booking', 'sport_center_sportcenter', 'user_user_groups', 'user_user_user_permissions')
AND column_name IN ('id', 'session_id', 'user_id', 'owner_id')
ORDER BY table_name, column_name;

