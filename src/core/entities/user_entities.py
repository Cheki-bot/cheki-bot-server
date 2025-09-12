from dataclasses import dataclass


@dataclass
class Role:
    id: int
    name: str
    description: str | None = None


@dataclass
class User:
    id: int
    email: str
    full_name: str
    password: str
    role_id: int = 1


@dataclass
class UserRole:
    id: int
    user: User
    role: Role
