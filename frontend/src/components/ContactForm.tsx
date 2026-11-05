import { useState } from "react";
import api from "../api";
import { useLang } from "../i18n";

function ContactForm() {
  const { t } = useLang();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("sending");

    try {
      await api.post("/contact", { name, email, message });
      setStatus("sent");
      setName("");
      setEmail("");
      setMessage("");
    } catch (error) {
      console.error("Failed to send message:", error);
      setStatus("error");
    }
  };

  return (
    <section className="contact-section" id="contact">
      <div className="contact-left">
        <h2 className="section-title">
          {t("contact_title_1")}
          <span className="grad-text">{t("contact_title_2")}</span>
        </h2>
        <p className="contact-sub">{t("contact_sub")}</p>

        <div className="contact-info">
          <div className="contact-item">
            <div className="contact-item-icon">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="2" y="4" width="20" height="16" rx="2" />
                <path d="m22 7-10 6L2 7" />
              </svg>
            </div>
            <div>
              <small>{t("contact_email_label")}</small>
              <span className="mono">cantek.contact@gmail.com</span>
            </div>
          </div>

          <div className="contact-item">
            <div className="contact-item-icon">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
            </div>
            <div>
              <small>{t("contact_based_label")}</small>
              <span>{t("city")}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="contact-card">
        <form className="contact-form" onSubmit={handleSubmit}>
          <input
            placeholder={t("form_name")}
            value={name}
            onChange={(e) => setName(e.target.value)}
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
            placeholder={t("form_message")}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
          />
          <button
            type="submit"
            className={`btn btn-grad btn-block ${status === "sending" ? "is-loading" : ""}`}
            disabled={status === "sending"}
          >
            {status === "sending" ? t("form_sending") : t("form_send")}
          </button>

          {status === "sent" && (
            <p className="contact-success">{t("form_success")}</p>
          )}
          {status === "error" && (
            <p className="contact-error">{t("form_error")}</p>
          )}
        </form>
      </div>
    </section>
  );
}

export default ContactForm;