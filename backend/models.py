from sqlalchemy import Column, DateTime, String, Integer, Date, Boolean, func, ForeignKey, false, true, text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum


Base = declarative_base()
metadata = Base.metadata

class AccountType(Enum):
    PERSONAL = "Personal" # Single user
    BUSINESS = "Business" # Multi-tenant

class Accounts(Base):
    __tablename__ = "accounts"

    account_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False) # AccountType PERSONAL or BUSINESS only via check constraint
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(Boolean, server_default=true(), nullable=False)

    memberships = relationship("AccountMemberships", back_populates="accounts")

    def __repr__(self):
        return f"Account ID: {self.account_id}, Account Name: {self.name}, Account Type: {self.type}"


class AccountMemberships(Base):
    __tablename__ = "account_memberships"

    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="NO ACTION"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    accounts = relationship("Accounts", back_populates="memberships")
    users = relationship("Users", back_populates="memberships")
    roles = relationship("Roles")

    def __repr__(self):
        return f"User ID: {self.user_id}, Role ID: {self.role_id}, Account ID: {self.account_id}"


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    email_verified = Column(Boolean, server_default=false(), nullable=False)
    phone = Column(String(15), nullable=False)
    dob = Column(Date, nullable=False)
    address = Column(String(150), nullable=False)
    city = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)
    zipcode = Column(String(20), nullable=False)
    country = Column(String(50),nullable=False)
    company = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    active = Column(Boolean, server_default=true(), nullable=False)

    roles = relationship("Roles", secondary="account_memberships", back_populates="users")
    memberships = relationship("AccountMemberships", back_populates="users")

    def __repr__(self):
        return f"User: {self.first_name} {self.last_name}, ID: {self.user_id}, Created: {self.created_at}"


class Roles(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(), nullable=True)

    users = relationship("Users", secondary="account_memberships", back_populates="roles")

    def __repr__(self):
        return f"Role ID: {self.role_id}, Role: {self.name}"


class EmailVerifications(Base):
    __tablename__ = "email_verifications"

    verification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(100), nullable=False, unique=True) # Stores token hash
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(
        DateTime(timezone=True),
        server_default=text("now() + interval '5 minutes'"),
        nullable=False
    )
    used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"Verification ID: {self.verification_id}, Token: {self.token}, Created: {self.created_at}, Used: {self.used_at if self.used_at else 'Not used'}"


class PasswordResets(Base):
    __tablename__ = "password_resets"

    reset_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token = Column(String(100), nullable=False, unique=True) # Stores token hash
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(
        DateTime(timezone=True),
        server_default=text("now() + interval '5 minutes'"),
        nullable=False
    )
    used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"Reset ID: {self.reset_id}, Token: {self.token}, Created: {self.created_at}, Used: {self.used_at if self.used_at else 'Not used'}"

