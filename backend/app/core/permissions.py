from enum import Enum


class Role(str, Enum):
    admin = "admin"
    customer = "customer"
    staff = "staff"


def is_admin(role: str | None) -> bool:
    return role == Role.admin
