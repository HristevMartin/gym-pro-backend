import enum


class RoleType(enum.Enum):
    default = "default"
    approver = "approver"
    admin = "admin"