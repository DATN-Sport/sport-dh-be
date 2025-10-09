from enum import Enum


class EnumType(str, Enum):
    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)

    @classmethod
    def list(cls):
        return list(map(lambda x: x.value, cls))

    def __str__(self):
        return self.value


class TypeEmailEnum(EnumType):
    REGISTER = "REGISTER"
    RESET_PASSWORD = "RESET_PASSWORD"


class RoleSystemEnum(EnumType):
    ADMIN = "ADMIN"
    OWNER = "OWNER"
    USER = "USER"


class StatusFieldEnum(EnumType):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class StatusBookingEnum(EnumType):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class SportTypeEnum(EnumType):
    FOOTBALL = "FOOTBALL"
    BADMINTON = "BADMINTON"
    TENNIS = "TENNIS"
    PICK_A_BALL = "PICK_A_BALL"
