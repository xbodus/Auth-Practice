"""Models used to valid user input"""

from pydantic import (
    BaseModel,
    SecretStr,
    EmailStr,
    PastDate,
    UUID7,
    Field,
)
from enum import Enum
from uuid6 import uuid7
from datetime import datetime, timezone


class UserPermissions(Enum):
    """Groups defined for account level permissions"""
    admin = "Admin"
    user = "User"
    guest = "Guest"

class MFAMethods(Enum):
    """Multifactor authentication methods"""
    otp = "One Time Password"
    authenticator = "Authenticator App"
    passkey = "Passkey"

class User(BaseModel):
    """User model validating user accounts"""
    id: UUID7 = Field(default_factory=lambda: uuid7(), validate_default=True)
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    username: str = Field(min_length=2, max_length=50)
    password: SecretStr = Field(min_length=8, max_length=50)
    dob: PastDate
    email: EmailStr
    phone: int = Field(min_length=10)
    mfa: bool = Field(default=False)
    mfa_method: MFAMethods | None = Field(default=None)
    permissions: UserPermissions = Field(default=UserPermissions.user)
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_access: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))