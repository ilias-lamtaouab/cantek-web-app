import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _send(msg: EmailMessage) -> None:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def send_reply_email(to_email: str, client_name: str, original_message: str, reply_text: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Re: your message to Cantek"
    msg["From"] = f"Cantek <{SMTP_USER}>"
    msg["To"] = to_email
    msg.set_content(
        f"Hello {client_name},\n\n"
        f"{reply_text}\n\n"
        f"Best regards,\n"
        f"The Cantek team\n\n"
        f"---\n"
        f"Your original message:\n"
        f"{original_message}\n"
    )
    _send(msg)


def send_reset_email(to_email: str, reset_token: str) -> None:
    link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    msg = EmailMessage()
    msg["Subject"] = "Reset your Cantek password"
    msg["From"] = f"Cantek <{SMTP_USER}>"
    msg["To"] = to_email
    msg.set_content(
        "Hello,\n\n"
        "We received a request to reset your Cantek password.\n"
        "Click the link below to choose a new one. It works for 15 minutes:\n\n"
        f"{link}\n\n"
        "If you did not ask for this, you can ignore this email.\n\n"
        "The Cantek team\n"
    )
    _send(msg)


def send_confirmation_email(order, pdf_bytes: bytes) -> None:
    lang = getattr(order, "language", "en")
    order_number = f"CTK-{order.id:05d}"

    msg = EmailMessage()
    msg["From"] = f"Cantek <{SMTP_USER}>"
    msg["To"] = order.client_email

    if lang == "fr":
        msg["Subject"] = f"Votre commande Cantek {order_number} est confirmée"
        msg.set_content(
            f"Bonjour {order.client_name},\n\n"
            f"Bonne nouvelle : votre commande pour « {order.service_name} » a été "
            f"confirmée par l’équipe Cantek.\n"
            f"Vous trouverez la confirmation dans le PDF ci-joint.\n\n"
            f"Nous vous contacterons bientôt pour discuter des prochaines étapes.\n\n"
            f"L’équipe Cantek\n"
        )
        filename = f"Cantek-commande-{order_number}.pdf"
    else:
        msg["Subject"] = f"Your Cantek order {order_number} is confirmed"
        msg.set_content(
            f"Hello {order.client_name},\n\n"
            f"Good news: your order for '{order.service_name}' has been confirmed "
            f"by the Cantek team.\n"
            f"You will find the confirmation in the attached PDF.\n\n"
            f"We will contact you soon to discuss the next steps.\n\n"
            f"The Cantek team\n"
        )
        filename = f"Cantek-order-{order_number}.pdf"

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )
    _send(msg)


def send_quote_email(quote, pdf_bytes: bytes, accept_url: str) -> None:
    from pdf_utils import money

    lang = quote.language if quote.language in ("en", "fr") else "en"
    quote_number = f"CTK-Q-{quote.id:05d}"

    msg = EmailMessage()
    msg["From"] = f"Cantek <{SMTP_USER}>"
    msg["To"] = quote.client_email

    if lang == "fr":
        msg["Subject"] = f"Votre devis Cantek {quote_number}"
        msg.set_content(
            f"Bonjour {quote.client_name},\n\n"
            f"Merci pour votre demande. Vous trouverez notre devis {quote_number} "
            f"en pièce jointe (total : {money(quote.total_price, lang)}).\n\n"
            f"Accepter ce devis (lien valable 30 jours) :\n"
            f"{accept_url}\n\n"
            f"Pour toute question, répondez simplement à cet email.\n\n"
            f"L’équipe Cantek\n"
        )
        filename = f"Cantek-devis-{quote_number}.pdf"
    else:
        msg["Subject"] = f"Your Cantek quote {quote_number}"
        msg.set_content(
            f"Hello {quote.client_name},\n\n"
            f"Thank you for your request. Please find our quote {quote_number} attached "
            f"(total: {money(quote.total_price, lang)}).\n\n"
            f"Accept this quote (link valid for 30 days):\n"
            f"{accept_url}\n\n"
            f"For any question, simply reply to this email.\n\n"
            f"The Cantek team\n"
        )
        filename = f"Cantek-quote-{quote_number}.pdf"

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )
    _send(msg)


EMAIL_LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo-email.png")


def send_admin_notification(
    recipients: list[str], subject: str, title: str, facts: list[tuple[str, str]], next_step: str
) -> None:
    """HTML email with the logo, a table of facts and a button, plus a plain-text version."""
    if not recipients:
        return

    admin_url = f"{FRONTEND_URL}/admin"

    plain = (
        f"{title}\n\n"
        + "".join(f"{label}: {value}\n" for label, value in facts)
        + f"\n{next_step}\n{admin_url}\n"
    )

    # Every value is escaped: client names and emails are typed by clients.
    logo_cid = make_msgid(domain="cantek.local")
    logo_html = ""
    if os.path.exists(EMAIL_LOGO_PATH):
        logo_html = (
            f'<img src="cid:{logo_cid[1:-1]}" alt="Cantek" width="120" '
            f'style="display:block;margin:0 auto 8px;border:0;">'
        )
    rows = "".join(
        f'<tr>'
        f'<td style="padding:10px 14px;border-bottom:1px solid #ECECF3;color:#5B5B6B;'
        f'font-size:14px;white-space:nowrap;">{escape(label)}</td>'
        f'<td style="padding:10px 14px;border-bottom:1px solid #ECECF3;color:#12121F;'
        f'font-size:14px;font-weight:bold;">{escape(value)}</td>'
        f'</tr>'
        for label, value in facts
    )
    html_body = f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#FAFAFC;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#FAFAFC;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="max-width:560px;background:#FFFFFF;border:1px solid #ECECF3;border-radius:16px;">
        <tr><td style="padding:28px 28px 8px;text-align:center;">
          {logo_html}
          <div style="height:4px;background:linear-gradient(90deg,#7C3AED,#EC4899);background-color:#7C3AED;border-radius:4px;margin:12px 0 20px;"></div>
          <h1 style="margin:0 0 6px;font-size:20px;color:#12121F;">{escape(title)}</h1>
          <p style="margin:0;color:#5B5B6B;font-size:14px;">{escape(subject)}</p>
        </td></tr>
        <tr><td style="padding:16px 28px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #ECECF3;border-radius:12px;border-collapse:separate;">
            {rows}
          </table>
        </td></tr>
        <tr><td style="padding:8px 28px 28px;text-align:center;">
          <p style="margin:0 0 18px;color:#5B5B6B;font-size:14px;">{escape(next_step)}</p>
          <a href="{escape(admin_url, quote=True)}"
             style="display:inline-block;padding:12px 28px;border-radius:100px;background:#7C3AED;
                    color:#FFFFFF;font-weight:bold;font-size:14px;text-decoration:none;">Open the admin</a>
        </td></tr>
      </table>
      <p style="margin:16px 0 0;color:#8A8A99;font-size:12px;">Cantek admin notification</p>
    </td></tr>
  </table>
</body>
</html>
"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"Cantek <{SMTP_USER}>"
    msg["To"] = ", ".join(recipients)
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")
    if logo_html:
        with open(EMAIL_LOGO_PATH, "rb") as logo_file:
            msg.get_payload()[1].add_related(
                logo_file.read(), maintype="image", subtype="png", cid=logo_cid
            )
    _send(msg)
