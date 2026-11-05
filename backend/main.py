from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from database import SessionLocal, engine, Base
from models import User, Product, ContactMessage
from schemas import (
    UserCreate, UserLogin, UserOut,
    ProductCreate, ProductOut,
    ContactMessageCreate, ContactMessageOut,
    ReplyCreate,
)
from auth import hash_password, verify_password, create_access_token, get_current_admin, ADMIN_EMAILS

Base.metadata.create_all(bind=engine)

# create_all does not add new columns to existing tables, so add them here once.
# Only on PostgreSQL: the tests use a fresh SQLite database where the column already exists.
if engine.dialect.name == "postgresql":
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS quote_only BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        connection.execute(text(
            "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS accept_token VARCHAR UNIQUE"
        ))
        connection.execute(text(
            "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS accept_token_expires_at TIMESTAMP"
        ))
        connection.execute(text(
            "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP"
        ))
        connection.execute(text(
            "ALTER TABLE quotes ADD COLUMN IF NOT EXISTS order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL"
        ))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Background jobs that run while the backend is up (see start_draft_cleanup below).
    stop_draft_cleanup = start_draft_cleanup()
    yield
    stop_draft_cleanup.set()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://cantek.localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello, my backend works!"}

@app.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/products", response_model=ProductOut)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    new_product = Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    updated: ProductCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

@app.post("/contact", response_model=ContactMessageOut)
def submit_contact(message: ContactMessageCreate, db: Session = Depends(get_db)):
    new_message = ContactMessage(**message.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@app.get("/contact", response_model=list[ContactMessageOut])
def list_contact_messages(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    return db.query(ContactMessage).order_by(ContactMessage.id.desc()).all()

@app.put("/contact/{message_id}/reply", response_model=ContactMessageOut)
def reply_to_message(
    message_id: int,
    data: ReplyCreate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    from email_utils import send_reply_email

    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    try:
        send_reply_email(message.email, message.name, message.message, data.reply)
    except Exception as error:
        print("Email error:", error)
        raise HTTPException(status_code=502, detail="Could not send the email")

    message.reply = data.reply
    message.replied_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message

from schemas import ForgotPasswordRequest, ResetPasswordRequest
from auth import create_reset_token, verify_reset_token


@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    from email_utils import send_reset_email

    user = db.query(User).filter(User.email == data.email).first()
    if user:
        try:
            token = create_reset_token(user.email)
            send_reset_email(user.email, token)
        except Exception as error:
            print("Reset email error:", error)

    return {"message": "If this email exists, a reset link has been sent."}


@app.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    email = verify_reset_token(data.token)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

from models import Order
from schemas import OrderCreate, OrderOut


def notify_admins(notice: dict) -> None:
    """Best effort: runs after the response, so a failed email never affects the client."""
    from email_utils import send_admin_notification

    try:
        send_admin_notification(ADMIN_EMAILS, **notice)
    except Exception:
        print("Admin notification email could not be sent")


def order_notification(order: Order) -> dict:
    from pdf_utils import money

    number = f"CTK-{order.id:05d}"
    return {
        "subject": f"New order {number}",
        "title": "A new order arrived.",
        "facts": [
            ("Order", number),
            ("Service", order.service_name),
            ("Client", order.client_name),
            ("Email", order.client_email),
            ("Total", f"{money(order.total_price, 'en')} "
                      f"(price {money(order.unit_price, 'en')}, discount {order.discount_percent:g}%)"),
            ("Client language", order.language.upper()),
        ],
        "next_step": "Open the Orders tab in the admin to confirm it.",
    }


@app.post("/orders", response_model=OrderOut)
def create_order(data: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Service not found")
    if product.quote_only:
        raise HTTPException(status_code=400, detail="This service is priced on quote. Please request a quote.")

    pending_count = (
        db.query(Order)
        .filter(Order.client_email == data.client_email, Order.status == "pending")
        .count()
    )
    if pending_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="You already have 3 pending orders. Please wait for confirmation.",
        )

    discount = product.discount_percent or 0
    total = round(product.price * (1 - discount / 100), 2)

    new_order = Order(
        client_name=data.client_name.strip(),
        client_email=data.client_email,
        product_id=product.id,
        service_name=(product.name_fr if data.language == "fr" and product.name_fr else product.name),
        unit_price=product.price,
        discount_percent=discount,
        total_price=total,
        note=(data.note or "").strip()[:1000] or None,
        language=data.language if data.language in ("en", "fr") else "en",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    background_tasks.add_task(notify_admins, order_notification(new_order))
    return new_order


@app.get("/orders", response_model=list[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    return db.query(Order).order_by(Order.id.desc()).all() 
@app.put("/orders/{order_id}/confirm", response_model=OrderOut)
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    from email_utils import send_confirmation_email
    from pdf_utils import generate_confirmation_pdf

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == "confirmed":
        raise HTTPException(status_code=400, detail="Order already confirmed")

    order.confirmed_at = datetime.utcnow()
    try:
        pdf_bytes = generate_confirmation_pdf(order)
        send_confirmation_email(order, pdf_bytes)
    except Exception as error:
        print("Confirmation error:", error)
        db.rollback()
        raise HTTPException(status_code=502, detail="Could not send the confirmation email")

    order.status = "confirmed"
    db.commit()
    db.refresh(order)
    return order      

import secrets
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import Request

from models import Quote, QuoteTask
from schemas import QuoteAnalyzeRequest, QuoteAnalyzeOut
from ai_utils import analyze_project, AiBusyError, AiUnavailableError

AI_RATE_LIMIT = 5
AI_RATE_WINDOW_SECONDS = 600
_ai_calls_by_ip: dict[str, deque] = defaultdict(deque)
_ai_calls_lock = Lock()

QUOTE_MESSAGES = {
    "rate_limited": {
        "en": "Too many requests. Please try again in a few minutes.",
        "fr": "Trop de demandes. Veuillez réessayer dans quelques minutes.",
    },
    "ai_busy": {
        "en": "Too many requests to our AI assistant. Please try again later.",
        "fr": "Trop de demandes envoyées à notre assistant IA. Veuillez réessayer plus tard.",
    },
    "ai_unavailable": {
        "en": "The project analysis is not available right now. Please try again later.",
        "fr": "L'analyse du projet n'est pas disponible pour le moment. Veuillez réessayer plus tard.",
    },
}


def quote_message(key: str, language: str) -> str:
    return QUOTE_MESSAGES[key]["fr" if language == "fr" else "en"]


def check_ai_rate_limit(ip: str) -> bool:
    now = time.monotonic()
    with _ai_calls_lock:
        calls = _ai_calls_by_ip[ip]
        while calls and now - calls[0] > AI_RATE_WINDOW_SECONDS:
            calls.popleft()
        if len(calls) >= AI_RATE_LIMIT:
            return False
        calls.append(now)
        return True


@app.post("/quotes/analyze", response_model=QuoteAnalyzeOut)
def analyze_quote(data: QuoteAnalyzeRequest, request: Request, db: Session = Depends(get_db)):
    language = data.language if data.language in ("en", "fr") else "en"

    ip = request.client.host if request.client else "unknown"
    if not check_ai_rate_limit(ip):
        raise HTTPException(status_code=429, detail=quote_message("rate_limited", language))

    try:
        tasks = analyze_project(data.description.strip(), language)
    except AiBusyError:
        raise HTTPException(status_code=429, detail=quote_message("ai_busy", language))
    except AiUnavailableError as error:
        print("Quote analysis error:", error)
        raise HTTPException(status_code=502, detail=quote_message("ai_unavailable", language))

    quote = Quote(
        public_token=secrets.token_urlsafe(24),
        client_name=data.client_name.strip(),
        client_email=data.client_email,
        description=data.description.strip(),
        language=language,
        status="draft",
    )
    db.add(quote)
    db.flush()

    for position, task in enumerate(tasks):
        db.add(QuoteTask(quote_id=quote.id, position=position, **task))

    db.commit()

    saved_tasks = (
        db.query(QuoteTask)
        .filter(QuoteTask.quote_id == quote.id)
        .order_by(QuoteTask.position)
        .all()
    )
    return {"quote_token": quote.public_token, "tasks": saved_tasks}


from datetime import timedelta
from models import Setting
from schemas import QuoteSubmitRequest, QuoteSubmitOut, DailyRateUpdate, DailyRateOut

DEFAULT_DAILY_RATE = 300.0
DRAFT_QUOTE_EXPIRY_HOURS = 2
MAX_PENDING_QUOTES_PER_EMAIL = 3

QUOTE_MESSAGES.update({
    "quote_not_found": {
        "en": "This quote request is invalid, expired or already sent. Please describe your project again.",
        "fr": "Cette demande de devis est invalide, expirée ou déjà envoyée. Veuillez décrire votre projet à nouveau.",
    },
    "invalid_tasks": {
        "en": "Some selected tasks are not part of this quote. Please select tasks from the list.",
        "fr": "Certaines tâches choisies ne font pas partie de ce devis. Veuillez choisir des tâches dans la liste.",
    },
    "too_many_pending": {
        "en": "You already have 3 pending quote requests. Please wait for our answer.",
        "fr": "Vous avez déjà 3 demandes de devis en attente. Veuillez attendre notre réponse.",
    },
})


def get_daily_rate(db: Session) -> tuple[float, bool]:
    """Returns (daily rate, True if it is the default because the admin never set one)."""
    setting = db.query(Setting).filter(Setting.key == "daily_rate").first()
    if not setting:
        return DEFAULT_DAILY_RATE, True
    return float(setting.value), False


def quote_notification(quote: Quote, task_count: int) -> dict:
    from pdf_utils import money

    number = f"CTK-Q-{quote.id:05d}"
    return {
        "subject": f"New quote request {number}",
        "title": "A new quote request arrived.",
        "facts": [
            ("Quote", number),
            ("Client", quote.client_name),
            ("Email", quote.client_email),
            ("Selected tasks", str(task_count)),
            ("Total days", f"{quote.total_days:g}"),
            ("Daily rate", money(quote.daily_rate, "en")),
            ("Total", money(quote.total_price, "en")),
            ("Client language", quote.language.upper()),
        ],
        "next_step": "Open the Quotes tab in the admin to review and send it.",
    }


@app.post("/quotes/submit", response_model=QuoteSubmitOut)
def submit_quote(data: QuoteSubmitRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    language = data.language if data.language in ("en", "fr") else "en"

    # Lock the row so the same token cannot be submitted twice at the same time.
    quote = (
        db.query(Quote)
        .filter(Quote.public_token == data.quote_token, Quote.status == "draft")
        .with_for_update()
        .first()
    )
    expiry_limit = datetime.utcnow() - timedelta(hours=DRAFT_QUOTE_EXPIRY_HOURS)
    if not quote or quote.created_at < expiry_limit:
        raise HTTPException(status_code=404, detail=quote_message("quote_not_found", language))

    language = quote.language

    pending_count = (
        db.query(Quote)
        .filter(Quote.client_email == quote.client_email, Quote.status == "pending")
        .count()
    )
    if pending_count >= MAX_PENDING_QUOTES_PER_EMAIL:
        raise HTTPException(status_code=429, detail=quote_message("too_many_pending", language))

    tasks = db.query(QuoteTask).filter(QuoteTask.quote_id == quote.id).all()
    tasks_by_id = {task.id: task for task in tasks}
    selected_ids = set(data.task_ids)
    if not selected_ids.issubset(tasks_by_id):
        raise HTTPException(status_code=400, detail=quote_message("invalid_tasks", language))

    # Days come from the saved AI tasks and the rate from the settings, never from the browser.
    daily_rate, _ = get_daily_rate(db)
    for task in tasks:
        task.selected = task.id in selected_ids
    total_days = sum(tasks_by_id[task_id].days for task_id in selected_ids)

    quote.daily_rate = daily_rate
    quote.total_days = total_days
    quote.total_price = round(total_days * daily_rate, 2)
    quote.status = "pending"
    quote.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(quote)
    background_tasks.add_task(notify_admins, quote_notification(quote, len(selected_ids)))
    return quote


@app.get("/settings/daily-rate", response_model=DailyRateOut)
def read_daily_rate(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    daily_rate, is_default = get_daily_rate(db)
    return {"daily_rate": daily_rate, "is_default": is_default}


@app.put("/settings/daily-rate", response_model=DailyRateOut)
def update_daily_rate(
    data: DailyRateUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    setting = db.query(Setting).filter(Setting.key == "daily_rate").first()
    if setting:
        setting.value = str(data.daily_rate)
    else:
        db.add(Setting(key="daily_rate", value=str(data.daily_rate)))
    db.commit()
    return {"daily_rate": data.daily_rate, "is_default": False}


from schemas import QuoteAdminOut, QuoteUpdate
from email_utils import FRONTEND_URL

ACCEPT_LINK_DAYS = 30


def selected_tasks(db: Session, quote_id: int) -> list[QuoteTask]:
    return (
        db.query(QuoteTask)
        .filter(QuoteTask.quote_id == quote_id, QuoteTask.selected == True)  # noqa: E712
        .order_by(QuoteTask.position)
        .all()
    )


def quote_admin_view(db: Session, quote: Quote) -> dict:
    view = {column.name: getattr(quote, column.name) for column in Quote.__table__.columns}
    view["tasks"] = selected_tasks(db, quote.id)
    return view


@app.get("/quotes", response_model=list[QuoteAdminOut])
def list_quotes(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    # Drafts are unfinished requests (the client never clicked Send), so they are not shown.
    quotes = db.query(Quote).filter(Quote.status != "draft").order_by(Quote.id.desc()).all()
    return [quote_admin_view(db, quote) for quote in quotes]


@app.put("/quotes/{quote_id}", response_model=QuoteAdminOut)
def update_quote(
    quote_id: int,
    data: QuoteUpdate,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    quote = db.query(Quote).filter(Quote.id == quote_id).with_for_update().first()
    if not quote or quote.status == "draft":
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status != "pending":
        raise HTTPException(status_code=400, detail="This quote was already sent and cannot be changed")

    tasks = selected_tasks(db, quote.id)
    tasks_by_id = {task.id: task for task in tasks}
    new_days = {item.id: item.days for item in data.tasks}
    if len(new_days) != len(data.tasks) or not set(new_days).issubset(tasks_by_id):
        raise HTTPException(status_code=400, detail="Some tasks are not part of this quote")

    for task_id, days in new_days.items():
        tasks_by_id[task_id].days = days

    # Recalculate on the server from the saved tasks and the new rate of this quote.
    quote.daily_rate = data.daily_rate
    quote.total_days = sum(task.days for task in tasks)
    quote.total_price = round(quote.total_days * quote.daily_rate, 2)
    db.commit()
    db.refresh(quote)
    return quote_admin_view(db, quote)


@app.post("/quotes/{quote_id}/send", response_model=QuoteAdminOut)
def send_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    from email_utils import send_quote_email
    from pdf_utils import generate_quote_pdf

    # Lock the row so a double click cannot send the email twice.
    quote = db.query(Quote).filter(Quote.id == quote_id).with_for_update().first()
    if not quote or quote.status == "draft":
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.status != "pending":
        raise HTTPException(status_code=400, detail="Quote already sent")

    tasks = selected_tasks(db, quote.id)
    quote.sent_at = datetime.utcnow()  # date printed on the PDF
    # One-time link for the client to accept online, separate from the public token.
    quote.accept_token = secrets.token_urlsafe(32)
    quote.accept_token_expires_at = quote.sent_at + timedelta(days=ACCEPT_LINK_DAYS)
    accept_url = f"{FRONTEND_URL}/accept-quote?token={quote.accept_token}"
    try:
        pdf_bytes = generate_quote_pdf(quote, tasks, accept_url)
        send_quote_email(quote, pdf_bytes, accept_url)
    except Exception as error:
        print("Quote email error:", error)
        db.rollback()
        raise HTTPException(status_code=502, detail="Could not send the quote email")

    quote.status = "sent"
    db.commit()
    db.refresh(quote)
    return quote_admin_view(db, quote)


from sqlalchemy import update
from schemas import QuoteAcceptRequest, QuoteAcceptPreview, QuoteAcceptResult

CUSTOM_SERVICE_NAMES = {"en": "Custom Development", "fr": "Développement sur mesure"}


def find_quote_to_accept(db: Session, token: str) -> Quote:
    """Checks the accept link. The same answers for every quote, so nothing is revealed about others."""
    quote = db.query(Quote).filter(Quote.accept_token == token).first()
    if not quote or quote.status not in ("sent", "accepted"):
        raise HTTPException(status_code=404, detail="This link is not valid")
    if quote.status == "accepted":
        raise HTTPException(status_code=409, detail="This quote was already accepted")
    if quote.accept_token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="This link has expired")
    return quote


@app.post("/quotes/accept/preview", response_model=QuoteAcceptPreview)
def preview_quote_to_accept(data: QuoteAcceptRequest, db: Session = Depends(get_db)):
    quote = find_quote_to_accept(db, data.token)
    return {
        "quote_number": f"CTK-Q-{quote.id:05d}",
        "client_name": quote.client_name,
        "language": quote.language,
        "tasks": selected_tasks(db, quote.id),
        "total_days": quote.total_days,
        "daily_rate": quote.daily_rate,
        "total_price": quote.total_price,
    }


@app.post("/quotes/accept", response_model=QuoteAcceptResult)
def accept_quote(data: QuoteAcceptRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    quote = find_quote_to_accept(db, data.token)
    now = datetime.utcnow()

    # Atomic: only one request can move the quote from "sent" to "accepted",
    # so the same link clicked twice at the same time cannot create two orders.
    result = db.execute(
        update(Quote)
        .where(Quote.id == quote.id, Quote.status == "sent")
        .values(status="accepted", accepted_at=now)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="This quote was already accepted")

    # The order uses the quote's own total, never a value from the browser.
    language = quote.language if quote.language in ("en", "fr") else "en"
    product = db.query(Product).filter(Product.quote_only == True).order_by(Product.id).first()  # noqa: E712
    if product and language == "fr" and product.name_fr:
        service = product.name_fr
    elif product:
        service = product.name
    else:
        service = CUSTOM_SERVICE_NAMES[language]
    quote_number = f"CTK-Q-{quote.id:05d}"
    quote_word = "devis" if language == "fr" else "quote"

    order = Order(
        client_name=quote.client_name,
        client_email=quote.client_email,
        product_id=product.id if product else None,
        service_name=f"{service} ({quote_word} {quote_number})",
        unit_price=quote.total_price,
        discount_percent=0,
        total_price=quote.total_price,
        language=language,
    )
    db.add(order)
    db.flush()
    db.refresh(quote)
    quote.order_id = order.id
    db.commit()

    background_tasks.add_task(notify_admins, accepted_quote_notification(quote, order))
    return {
        "quote_number": quote_number,
        "order_number": f"CTK-{order.id:05d}",
        "total_price": order.total_price,
    }


def accepted_quote_notification(quote: Quote, order: Order) -> dict:
    from pdf_utils import money

    quote_number = f"CTK-Q-{quote.id:05d}"
    order_number = f"CTK-{order.id:05d}"
    return {
        "subject": f"Quote {quote_number} accepted, new order {order_number}",
        "title": "A client accepted a quote online.",
        "facts": [
            ("Quote", quote_number),
            ("New order", f"{order_number} (pending)"),
            ("Client", quote.client_name),
            ("Email", quote.client_email),
            ("Total days", f"{quote.total_days:g}"),
            ("Total", money(order.total_price, "en")),
            ("Client language", quote.language.upper()),
        ],
        "next_step": "Open the Orders tab in the admin to confirm the order.",
    }


import threading

DRAFT_CLEANUP_DAYS = 7
DRAFT_CLEANUP_INTERVAL_SECONDS = 24 * 60 * 60


def delete_old_drafts(db: Session) -> int:
    """Deletes draft quotes (analysed but never submitted) older than 7 days, with their tasks.
    Pending, sent and accepted quotes are never touched."""
    limit = datetime.utcnow() - timedelta(days=DRAFT_CLEANUP_DAYS)
    old_ids = [
        quote_id for (quote_id,) in
        db.query(Quote.id).filter(Quote.status == "draft", Quote.created_at < limit).all()
    ]
    if not old_ids:
        return 0

    db.query(QuoteTask).filter(QuoteTask.quote_id.in_(old_ids)).delete(synchronize_session=False)
    deleted = (
        db.query(Quote)
        .filter(Quote.id.in_(old_ids), Quote.status == "draft")  # status checked again on delete
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def start_draft_cleanup() -> threading.Event:
    """Runs the cleanup when the backend starts, then once a day. Set the returned event to stop."""
    stop = threading.Event()

    def run():
        while True:
            db = SessionLocal()
            try:
                deleted = delete_old_drafts(db)
                if deleted:
                    print(f"Deleted {deleted} old draft quote(s)")
            except Exception:
                db.rollback()
                print("Draft quote cleanup failed")
            finally:
                db.close()
            if stop.wait(DRAFT_CLEANUP_INTERVAL_SECONDS):
                break

    threading.Thread(target=run, name="draft-cleanup", daemon=True).start()
    return stop
