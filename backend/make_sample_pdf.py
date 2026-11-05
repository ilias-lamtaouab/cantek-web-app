from datetime import datetime
from types import SimpleNamespace

from pdf_utils import generate_confirmation_pdf

order = SimpleNamespace(
    id=1,
    client_name="Jane Doe",
    client_email="jane.doe@example.com",
    service_name="Custom Development",
    unit_price=3500.0,
    discount_percent=10.0,
    total_price=3150.0,
    note="Sample order used to preview the PDF layout.",
    confirmed_at=datetime.utcnow(),
)

with open("sample.pdf", "wb") as f:
    f.write(generate_confirmation_pdf(order))

print("sample.pdf created")