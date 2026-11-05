import io
import os
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

# Change these in one place when the real details are confirmed
CURRENCY = "$"
COMPANY_NAME = "Cantek"
COMPANY_EMAIL = "cantek.contact@gmail.com"

VIOLET = HexColor("#7C3AED")
INK = HexColor("#12121F")
SLATE = HexColor("#5B5B6B")
SOFT = HexColor("#F4F1FF")
LINE = HexColor("#ECECF3")
GREEN = HexColor("#16A34A")

LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

TEXTS = {
    "en": {
        "title": "Order Confirmation",
        "order_no": "Order No.",
        "issued": "Issued on",
        "client": "CLIENT",
        "from": "FROM",
        "status": "STATUS: CONFIRMED",
        "col_service": "SERVICE",
        "col_unit": "UNIT PRICE",
        "col_discount": "DISCOUNT",
        "col_total": "TOTAL",
        "unit_price": "Unit price",
        "discount": "Discount",
        "total": "Total",
        "note": "YOUR NOTE",
        "message": (
            "Thank you for your order. The Cantek team has reviewed your request and "
            "confirmed it. We will contact you soon to discuss the next steps."
        ),
        "disclaimer": (
            "This document confirms an order request. "
            "It is not a payment receipt or an invoice."
        ),
        "tagline": "Software and AI, built around you.",
        "city": "Montreal · Marrakech",
    },
    "fr": {
        "title": "Confirmation de commande",
        "order_no": "Commande n°",
        "issued": "Émise le",
        "client": "CLIENT",
        "from": "DE",
        "status": "STATUT : CONFIRMÉE",
        "col_service": "SERVICE",
        "col_unit": "PRIX UNITAIRE",
        "col_discount": "REMISE",
        "col_total": "TOTAL",
        "unit_price": "Prix unitaire",
        "discount": "Remise",
        "total": "Total",
        "note": "VOTRE NOTE",
        "message": (
            "Merci pour votre commande. L’équipe Cantek a examiné votre demande et "
            "l’a confirmée. Nous vous contacterons bientôt pour discuter des "
            "prochaines étapes."
        ),
        "disclaimer": (
            "Ce document confirme une demande de commande. "
            "Il ne constitue ni un reçu de paiement ni une facture."
        ),
        "tagline": "Logiciels et IA, pensés pour vous.",
        "city": "Montréal · Marrakech",
    },
}

FR_MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def money(value: float, lang: str) -> str:
    if lang == "fr":
        text = f"{value:,.2f}".replace(",", " ").replace(".", ",")
        return f"{text} {CURRENCY}"
    return f"{CURRENCY}{value:,.2f}"


def percent(value: float, lang: str) -> str:
    return f"{value:g} %" if lang == "fr" else f"{value:g}%"


def format_date(date: datetime, lang: str) -> str:
    if lang == "fr":
        return f"{date.day} {FR_MONTHS[date.month - 1]} {date.year}"
    return date.strftime("%d %B %Y")


def _gradient_line(c, x, y, width, height=1.2 * mm):
    start = (124, 58, 237)
    end = (236, 72, 153)
    steps = 120
    seg = width / steps
    for i in range(steps):
        t = i / (steps - 1)
        r = start[0] + (end[0] - start[0]) * t
        g = start[1] + (end[1] - start[1]) * t
        b = start[2] + (end[2] - start[2]) * t
        c.setFillColorRGB(r / 255, g / 255, b / 255)
        c.rect(x + i * seg, y, seg + 0.4, height, stroke=0, fill=1)


def generate_confirmation_pdf(order) -> bytes:
    lang = getattr(order, "language", "en")
    if lang not in TEXTS:
        lang = "en"
    tx = TEXTS[lang]

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 20 * mm
    right = page_w - margin
    content_w = page_w - 2 * margin
    top = page_h - margin

    order_number = f"CTK-{order.id:05d}"
    issued_date = order.confirmed_at or datetime.utcnow()
    issued = format_date(issued_date, lang)

    # ---------- Header ----------
    logo_h = 26 * mm
    if os.path.exists(LOGO_PATH):
        logo = ImageReader(LOGO_PATH)
        iw, ih = logo.getSize()
        logo_w = logo_h * iw / ih
        c.drawImage(logo, margin, top - logo_h, width=logo_w, height=logo_h, mask="auto")

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawRightString(right, top - 9 * mm, tx["title"])
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawRightString(right, top - 16 * mm, f"{tx['order_no']} {order_number}")
    c.drawRightString(right, top - 21.5 * mm, f"{tx['issued']} {issued}")

    line_y = top - logo_h - 7 * mm
    _gradient_line(c, margin, line_y, content_w)

    # ---------- Client and company ----------
    y = line_y - 14 * mm
    col2_x = margin + content_w / 2 + 8 * mm

    c.setFillColor(SLATE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, tx["client"])
    c.drawString(col2_x, y, tx["from"])

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y - 6 * mm, order.client_name[:40])
    c.drawString(col2_x, y - 6 * mm, COMPANY_NAME)

    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawString(margin, y - 11.5 * mm, order.client_email[:48])
    c.drawString(col2_x, y - 11.5 * mm, COMPANY_EMAIL)
    c.drawString(col2_x, y - 16.5 * mm, tx["city"])

    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y - 18 * mm, tx["status"])

    # ---------- Service table ----------
    y = y - 32 * mm
    unit_right = margin + content_w * 0.62
    disc_right = margin + content_w * 0.80
    total_right = right - 4 * mm

    c.setFillColor(SOFT)
    c.roundRect(margin, y - 3 * mm, content_w, 10 * mm, 2.5 * mm, stroke=0, fill=1)
    c.setFillColor(VIOLET)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 4 * mm, y + 0.5 * mm, tx["col_service"])
    c.drawRightString(unit_right, y + 0.5 * mm, tx["col_unit"])
    c.drawRightString(disc_right, y + 0.5 * mm, tx["col_discount"])
    c.drawRightString(total_right, y + 0.5 * mm, tx["col_total"])

    y -= 14 * mm
    service_lines = simpleSplit(order.service_name, "Helvetica-Bold", 11, content_w * 0.40)
    if len(service_lines) > 2:
        service_lines = [service_lines[0], service_lines[1] + "..."]
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11)
    if len(service_lines) <= 1:
        c.drawString(margin + 4 * mm, y, service_lines[0] if service_lines else "")
    else:
        c.drawString(margin + 4 * mm, y + 2 * mm, service_lines[0])
        c.drawString(margin + 4 * mm, y - 2.5 * mm, service_lines[1])
    c.setFont("Helvetica", 11)
    c.drawRightString(unit_right, y, money(order.unit_price, lang))
    c.drawRightString(disc_right, y, percent(order.discount_percent, lang))
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(total_right, y, money(order.total_price, lang))

    y -= 5 * mm
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.line(margin, y, right, y)

    # ---------- Totals ----------
    discount_amount = round(order.unit_price * order.discount_percent / 100, 2)
    label_x = right - 72 * mm

    y -= 9 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawString(label_x, y, tx["unit_price"])
    c.drawRightString(total_right, y, money(order.unit_price, lang))

    y -= 6.5 * mm
    c.drawString(label_x, y, f"{tx['discount']} ({percent(order.discount_percent, lang)})")
    c.drawRightString(total_right, y, f"-{money(discount_amount, lang)}")

    y -= 4.5 * mm
    c.line(label_x, y, right, y)

    y -= 8 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(label_x, y, tx["total"])
    c.setFillColor(VIOLET)
    c.drawRightString(total_right, y, money(order.total_price, lang))

    # ---------- Client note ----------
    if order.note:
        y -= 16 * mm
        c.setFillColor(SLATE)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(margin, y, tx["note"])
        c.setFillColor(INK)
        c.setFont("Helvetica", 10)
        note_lines = simpleSplit(order.note, "Helvetica", 10, content_w)[:6]
        y -= 6 * mm
        for line in note_lines:
            c.drawString(margin, y, line)
            y -= 5 * mm
        y += 5 * mm

    # ---------- Message box ----------
    y -= 16 * mm
    box_h = 28 * mm
    c.setFillColor(SOFT)
    c.roundRect(margin, y - box_h + 8 * mm, content_w, box_h, 3 * mm, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    ty = y + 1 * mm
    for line in simpleSplit(tx["message"], "Helvetica", 10, content_w - 12 * mm):
        c.drawString(margin + 6 * mm, ty, line)
        ty -= 5 * mm

    c.setFillColor(SLATE)
    c.setFont("Helvetica-Oblique", 8.5)
    ty -= 2 * mm
    for line in simpleSplit(tx["disclaimer"], "Helvetica-Oblique", 8.5, content_w - 12 * mm):
        c.drawString(margin + 6 * mm, ty, line)
        ty -= 4.5 * mm

    # ---------- Footer ----------
    c.setStrokeColor(LINE)
    c.line(margin, 22 * mm, right, 22 * mm)
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    c.drawCentredString(
        page_w / 2, 16 * mm, f"{COMPANY_NAME}  |  {COMPANY_EMAIL}  |  {tx['city']}"
    )
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawCentredString(page_w / 2, 11.5 * mm, tx["tagline"])

    c.showPage()
    c.save()
    return buffer.getvalue()


QUOTE_TEXTS = {
    "en": {
        "title": "Quote",
        "quote_no": "Quote No.",
        "continued": "continued",
        "project": "PROJECT DESCRIPTION",
        "col_task": "TASK",
        "col_days": "DAYS",
        "total_days": "Total days",
        "daily_rate": "Daily rate",
        "total": "Total",
        "message": (
            "Thank you for your request. This quote is based on the tasks you selected. "
            "To accept it, click the button below or the link in our email. "
            "For any question, simply reply to our email."
        ),
        "accept_button": "Accept this quote",
        "disclaimer": "This document is a quote. It is not a payment receipt or an invoice.",
    },
    "fr": {
        "title": "Devis",
        "quote_no": "Devis n°",
        "issued": "Émis le",
        "continued": "suite",
        "project": "DESCRIPTION DU PROJET",
        "col_task": "TÂCHE",
        "col_days": "JOURS",
        "total_days": "Nombre total de jours",
        "daily_rate": "Tarif journalier",
        "total": "Total",
        "message": (
            "Merci pour votre demande. Ce devis est basé sur les tâches que vous avez choisies. "
            "Pour l’accepter, cliquez sur le bouton ci-dessous ou sur le lien de notre email. "
            "Pour toute question, répondez simplement à notre email."
        ),
        "accept_button": "Accepter ce devis",
        "disclaimer": "Ce document est un devis. Il ne constitue ni un reçu de paiement ni une facture.",
    },
}


def days_label(days: float, lang: str) -> str:
    if lang == "fr":
        return f"{days:g}".replace(".", ",") + (" jour" if days < 2 else " jours")
    return f"{days:g}" + (" day" if days <= 1 else " days")


def _wrap(text: str, font: str, size: float, width: float) -> list[str]:
    lines = []
    for paragraph in (text or "").splitlines() or [""]:
        lines.extend(simpleSplit(paragraph, font, size, width) or [""])
    return lines


def generate_quote_pdf(quote, tasks, accept_url: str | None = None) -> bytes:
    lang = quote.language if quote.language in QUOTE_TEXTS else "en"
    tx = {**TEXTS[lang], **QUOTE_TEXTS[lang]}

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_w, page_h = A4
    margin = 20 * mm
    right = page_w - margin
    content_w = page_w - 2 * margin
    top = page_h - margin
    bottom_limit = 32 * mm  # keep clear of the footer

    quote_number = f"CTK-Q-{quote.id:05d}"
    issued = format_date(quote.sent_at or datetime.utcnow(), lang)

    def draw_footer():
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.line(margin, 22 * mm, right, 22 * mm)
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 9)
        c.drawCentredString(
            page_w / 2, 16 * mm, f"{COMPANY_NAME}  |  {COMPANY_EMAIL}  |  {tx['city']}"
        )
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawCentredString(page_w / 2, 11.5 * mm, tx["tagline"])

    state = {"y": 0.0}

    def need(height: float):
        """Start a new page when the next block does not fit."""
        if state["y"] - height >= bottom_limit:
            return
        draw_footer()
        c.showPage()
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 9)
        c.drawRightString(right, top, f"{quote_number} ({tx['continued']})")
        _gradient_line(c, margin, top - 5 * mm, content_w, height=0.8 * mm)
        state["y"] = top - 14 * mm

    # ---------- Header (same layout as the order confirmation) ----------
    logo_h = 26 * mm
    if os.path.exists(LOGO_PATH):
        logo = ImageReader(LOGO_PATH)
        iw, ih = logo.getSize()
        logo_w = logo_h * iw / ih
        c.drawImage(logo, margin, top - logo_h, width=logo_w, height=logo_h, mask="auto")

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawRightString(right, top - 9 * mm, tx["title"])
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawRightString(right, top - 16 * mm, f"{tx['quote_no']} {quote_number}")
    c.drawRightString(right, top - 21.5 * mm, f"{tx['issued']} {issued}")

    line_y = top - logo_h - 7 * mm
    _gradient_line(c, margin, line_y, content_w)

    # ---------- Client and company ----------
    y = line_y - 14 * mm
    col2_x = margin + content_w / 2 + 8 * mm

    c.setFillColor(SLATE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, tx["client"])
    c.drawString(col2_x, y, tx["from"])

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y - 6 * mm, quote.client_name[:40])
    c.drawString(col2_x, y - 6 * mm, COMPANY_NAME)

    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawString(margin, y - 11.5 * mm, quote.client_email[:48])
    c.drawString(col2_x, y - 11.5 * mm, COMPANY_EMAIL)
    c.drawString(col2_x, y - 16.5 * mm, tx["city"])

    # ---------- Project description ----------
    state["y"] = y - 28 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, state["y"], tx["project"])
    state["y"] -= 6 * mm
    for line in _wrap(quote.description, "Helvetica", 10, content_w):
        need(5 * mm)
        c.setFillColor(INK)
        c.setFont("Helvetica", 10)
        c.drawString(margin, state["y"], line)
        state["y"] -= 5 * mm

    # ---------- Task table ----------
    days_right = right - 4 * mm
    text_w = content_w * 0.75

    def draw_table_head():
        c.setFillColor(SOFT)
        c.roundRect(margin, state["y"] - 3 * mm, content_w, 10 * mm, 2.5 * mm, stroke=0, fill=1)
        c.setFillColor(VIOLET)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin + 4 * mm, state["y"] + 0.5 * mm, tx["col_task"])
        c.drawRightString(days_right, state["y"] + 0.5 * mm, tx["col_days"])
        state["y"] -= 12 * mm

    state["y"] -= 8 * mm
    need(30 * mm)
    draw_table_head()

    for task in tasks:
        title_lines = _wrap(task.title, "Helvetica-Bold", 11, text_w)
        desc_lines = _wrap(task.description, "Helvetica", 9, text_w)
        row_h = len(title_lines) * 5 * mm + len(desc_lines) * 4.3 * mm + 4 * mm
        if state["y"] - row_h < bottom_limit:
            need(row_h + 14 * mm)
            draw_table_head()

        row_top = state["y"]
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        for line in title_lines:
            c.drawString(margin + 4 * mm, state["y"], line)
            state["y"] -= 5 * mm
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 9)
        for line in desc_lines:
            c.drawString(margin + 4 * mm, state["y"], line)
            state["y"] -= 4.3 * mm
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(days_right, row_top, days_label(task.days, lang))

        state["y"] -= 1 * mm
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.line(margin, state["y"], right, state["y"])
        state["y"] -= 6 * mm

    # ---------- Totals ----------
    need(36 * mm)
    label_x = right - 72 * mm
    state["y"] -= 3 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 10)
    c.drawString(label_x, state["y"], tx["total_days"])
    c.drawRightString(days_right, state["y"], days_label(quote.total_days, lang))

    state["y"] -= 6.5 * mm
    c.drawString(label_x, state["y"], tx["daily_rate"])
    c.drawRightString(days_right, state["y"], money(quote.daily_rate, lang))

    state["y"] -= 4.5 * mm
    c.setStrokeColor(LINE)
    c.line(label_x, state["y"], right, state["y"])

    state["y"] -= 8 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(label_x, state["y"], tx["total"])
    c.setFillColor(VIOLET)
    c.drawRightString(days_right, state["y"], money(quote.total_price, lang))

    # ---------- Message box ----------
    message_lines = simpleSplit(tx["message"], "Helvetica", 10, content_w - 12 * mm)
    disclaimer_lines = simpleSplit(tx["disclaimer"], "Helvetica-Oblique", 8.5, content_w - 12 * mm)
    button_h = 9 * mm if accept_url else 0
    box_h = len(message_lines) * 5 * mm + len(disclaimer_lines) * 4.5 * mm + 12 * mm
    if accept_url:
        box_h += button_h + 5 * mm
    state["y"] -= 12 * mm
    need(box_h)

    c.setFillColor(SOFT)
    c.roundRect(margin, state["y"] - box_h, content_w, box_h, 3 * mm, stroke=0, fill=1)
    ty = state["y"] - 7 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica", 10)
    for line in message_lines:
        c.drawString(margin + 6 * mm, ty, line)
        ty -= 5 * mm

    if accept_url:
        # Clickable button that opens the accept page
        button_w = c.stringWidth(tx["accept_button"], "Helvetica-Bold", 10) + 14 * mm
        button_x = margin + 6 * mm
        button_y = ty - button_h + 1 * mm
        c.setFillColor(VIOLET)
        c.roundRect(button_x, button_y, button_w, button_h, button_h / 2, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(button_x + button_w / 2, button_y + 3.2 * mm, tx["accept_button"])
        c.linkURL(accept_url, (button_x, button_y, button_x + button_w, button_y + button_h), relative=0)
        ty = button_y - 5 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica-Oblique", 8.5)
    ty -= 2 * mm
    for line in disclaimer_lines:
        c.drawString(margin + 6 * mm, ty, line)
        ty -= 4.5 * mm

    draw_footer()
    c.showPage()
    c.save()
    return buffer.getvalue()