from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    discount_percent: float = 0
    photo_url: str | None = None
    name_fr: str | None = None
    description_fr: str | None = None
    quote_only: bool = False


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    discount_percent: float
    photo_url: str | None
    name_fr: str | None = None
    description_fr: str | None = None
    quote_only: bool = False

    class Config:
        from_attributes = True


class ContactMessageCreate(BaseModel):
    name: str
    email: EmailStr
    message: str


class ContactMessageOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    message: str
    reply: str | None = None
    replied_at: datetime | None = None

    class Config:
        from_attributes = True


class ReplyCreate(BaseModel):
    reply: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class OrderCreate(BaseModel):
    language: str = "en"
    client_name: str
    client_email: EmailStr
    product_id: int
    note: str | None = None


class OrderOut(BaseModel):
    id: int
    client_name: str
    client_email: EmailStr
    product_id: int | None = None
    service_name: str
    unit_price: float
    discount_percent: float
    total_price: float
    note: str | None = None
    status: str
    created_at: datetime
    confirmed_at: datetime | None = None

    class Config:
        from_attributes = True

class QuoteAnalyzeRequest(BaseModel):
    language: str = "en"
    client_name: str = Field(min_length=1, max_length=100)
    client_email: EmailStr
    description: str = Field(min_length=30, max_length=3000)


class QuoteTaskOut(BaseModel):
    id: int
    title: str
    description: str
    days: float

    class Config:
        from_attributes = True


class QuoteAnalyzeOut(BaseModel):
    quote_token: str
    tasks: list[QuoteTaskOut]


class QuoteSubmitRequest(BaseModel):
    quote_token: str = Field(min_length=1, max_length=100)
    task_ids: list[int] = Field(min_length=1, max_length=15)
    language: str = "en"


class QuoteSubmitOut(BaseModel):
    id: int
    status: str
    total_days: float

    class Config:
        from_attributes = True


class DailyRateUpdate(BaseModel):
    daily_rate: float = Field(gt=0, le=100000)


class DailyRateOut(BaseModel):
    daily_rate: float
    is_default: bool


class QuoteAdminOut(BaseModel):
    id: int
    client_name: str
    client_email: EmailStr
    description: str
    language: str
    status: str
    daily_rate: float | None = None
    total_days: float | None = None
    total_price: float | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    sent_at: datetime | None = None
    accepted_at: datetime | None = None
    order_id: int | None = None
    tasks: list[QuoteTaskOut]


class QuoteAcceptRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class QuoteAcceptTask(BaseModel):
    title: str
    description: str
    days: float

    class Config:
        from_attributes = True


class QuoteAcceptPreview(BaseModel):
    quote_number: str
    client_name: str
    language: str
    tasks: list[QuoteAcceptTask]
    total_days: float
    daily_rate: float
    total_price: float


class QuoteAcceptResult(BaseModel):
    quote_number: str
    order_number: str
    total_price: float


class QuoteTaskDaysUpdate(BaseModel):
    id: int
    days: float = Field(ge=0.5, le=60, multiple_of=0.5)


class QuoteUpdate(BaseModel):
    daily_rate: float = Field(gt=0, le=100000)
    tasks: list[QuoteTaskDaysUpdate] = Field(max_length=15)
