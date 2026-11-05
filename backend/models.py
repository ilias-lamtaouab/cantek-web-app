from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)
    photo_url = Column(String, nullable=True)
    name_fr = Column(String, nullable=True)
    description_fr = Column(String, nullable=True)
    quote_only = Column(Boolean, default=False, server_default="false", nullable=False)


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    message = Column(String, nullable=False)
    reply = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)

from datetime import datetime
from sqlalchemy import ForeignKey


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    service_name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0)
    total_price = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    language = Column(String, default="en", nullable=False)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    public_token = Column(String, unique=True, index=True, nullable=False)
    client_name = Column(String, nullable=False)
    client_email = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    language = Column(String, default="en", nullable=False)
    status = Column(String, default="draft", nullable=False)
    daily_rate = Column(Float, nullable=True)
    total_days = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    accept_token = Column(String, unique=True, index=True, nullable=True)
    accept_token_expires_at = Column(DateTime, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)


class QuoteTask(Base):
    __tablename__ = "quote_tasks"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    days = Column(Float, nullable=False)
    selected = Column(Boolean, default=False, nullable=False)
