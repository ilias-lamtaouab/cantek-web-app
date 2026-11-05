import { useState } from "react";
import { isAxiosError } from "axios";
import api from "../api";
import { useLang } from "../i18n";

interface OrderModalProps {
  product: {
    id: number;
    name: string;
    price: number;
    discount_percent: number;
  };
  onClose: () => void;
}

function OrderModal({ product, onClose }: OrderModalProps) {
  const { t, lang } = useLang();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const finalPrice = product.price - (product.price * product.discount_percent) / 100;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSending(true);

    try {
      await api.post("/orders", {
        client_name: name,
        client_email: email,
        product_id: product.id,
        note: note || null,
        language: lang,
      });
      setSent(true);
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : undefined;
      setError(typeof detail === "string" ? detail : t("form_error"));
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <div className="product-form-overlay" onClick={onClose}>
        <div className="product-form order-modal" onClick={(e) => e.stopPropagation()}>
          <div className="status-icon success">✓</div>
          <h3>{t("order_sent_title")}</h3>
          <p className="auth-success">{t("order_sent_text")}</p>
          <div className="form-actions single">
            <button type="button" className="btn btn-ink" onClick={onClose}>{t("order_close")}</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="product-form-overlay" onClick={onClose}>
      <form
        className="product-form order-modal"
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>
          {t("order_title")}
          {product.name}
        </h3>
        <div className="total-bar">
          <span>{t("order_total")}</span>
          <strong>${finalPrice.toFixed(2)}</strong>
        </div>

        <input
          type="text"
          placeholder={t("form_name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={80}
          required
        />
        <input
          type="email"
          placeholder={t("form_email")}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <textarea
          placeholder={t("order_note")}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          maxLength={1000}
        />

        {error && <p className="auth-message">{error}</p>}

        <div className="form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose}>{t("order_cancel")}</button>
          <button type="submit" className={`btn btn-grad ${sending ? "is-loading" : ""}`} disabled={sending}>
            {sending ? t("order_sending") : t("order_send")}
          </button>
        </div>
      </form>
    </div>
  );
}

export default OrderModal;