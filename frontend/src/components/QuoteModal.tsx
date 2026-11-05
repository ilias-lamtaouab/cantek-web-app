import { useState } from "react";
import { isAxiosError } from "axios";
import api from "../api";
import { useLang } from "../i18n";

interface QuoteTask {
  id: number;
  title: string;
  description: string;
  days: number;
}

interface QuoteModalProps {
  serviceName: string;
  onClose: () => void;
}

const MIN_DESCRIPTION = 30;
const MAX_DESCRIPTION = 3000;
// The server stops the AI after 45 seconds; this is a safety net if the server never answers.
const REQUEST_TIMEOUT_MS = 75000;

function QuoteModal({ serviceName, onClose }: QuoteModalProps) {
  const { t, lang } = useLang();
  const [step, setStep] = useState<"describe" | "checklist" | "sent">("describe");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [description, setDescription] = useState("");
  const [quoteToken, setQuoteToken] = useState("");
  const [tasks, setTasks] = useState<QuoteTask[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Days are only displayed here. The server recalculates everything from its own copy.
  const selectedDays = tasks
    .filter((task) => selectedIds.includes(task.id))
    .reduce((sum, task) => sum + task.days, 0);

  const formatDays = (days: number) => {
    const singular = lang === "fr" ? days < 2 : days <= 1;
    return days.toLocaleString(lang) + (singular ? t("quote_day") : t("quote_days"));
  };

  const showError = (err: unknown) => {
    if (isAxiosError(err) && !err.response) {
      // Timeout or no connection: there is no message from the server to show.
      setError(t("quote_unavailable"));
      return;
    }
    const detail = isAxiosError(err) ? err.response?.data?.detail : null;
    setError(typeof detail === "string" ? detail : t("form_error"));
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSending(true);

    try {
      const response = await api.post(
        "/quotes/analyze",
        {
          client_name: name,
          client_email: email,
          description,
          language: lang,
        },
        { timeout: REQUEST_TIMEOUT_MS }
      );
      setQuoteToken(response.data.quote_token);
      setTasks(response.data.tasks);
      setSelectedIds(response.data.tasks.map((task: QuoteTask) => task.id));
      setStep("checklist");
    } catch (err) {
      showError(err);
    } finally {
      setSending(false);
    }
  };

  const toggleTask = (id: number) => {
    setSelectedIds((ids) =>
      ids.includes(id) ? ids.filter((other) => other !== id) : [...ids, id]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (selectedIds.length === 0) {
      setError(t("quote_none_selected"));
      return;
    }
    setSending(true);

    try {
      await api.post(
        "/quotes/submit",
        {
          quote_token: quoteToken,
          task_ids: selectedIds,
          language: lang,
        },
        { timeout: REQUEST_TIMEOUT_MS }
      );
      setStep("sent");
    } catch (err) {
      showError(err);
    } finally {
      setSending(false);
    }
  };

  const handleBack = () => {
    setError(null);
    setStep("describe");
  };

  // Do not lose the checklist or a running request with a click outside the box.
  const handleOverlayClick = () => {
    if (!sending && step !== "checklist") onClose();
  };

  if (step === "sent") {
    return (
      <div className="product-form-overlay" onClick={onClose}>
        <div className="product-form order-modal" onClick={(e) => e.stopPropagation()}>
          <div className="status-icon success">✓</div>
          <h3>{t("quote_sent_title")}</h3>
          <p className="auth-success">{t("quote_sent_text")}</p>
          <div className="form-actions single">
            <button type="button" className="btn btn-ink" onClick={onClose}>{t("order_close")}</button>
          </div>
        </div>
      </div>
    );
  }

  if (step === "checklist") {
    return (
      <div className="product-form-overlay" onClick={handleOverlayClick}>
        <form
          className="product-form order-modal quote-modal"
          onSubmit={handleSubmit}
          onClick={(e) => e.stopPropagation()}
        >
          <h3>{t("quote_checklist_title")}</h3>
          <p className="quote-hint">{t("quote_checklist_hint")}</p>

          <div className="quote-task-list">
            {tasks.map((task) => (
              <label
                key={task.id}
                className={`quote-task ${selectedIds.includes(task.id) ? "selected" : ""}`}
              >
                <input
                  type="checkbox"
                  className="check"
                  checked={selectedIds.includes(task.id)}
                  onChange={() => toggleTask(task.id)}
                />
                <span className="quote-task-text">
                  <strong>{task.title}</strong>
                  <span className="quote-task-desc">{task.description}</span>
                </span>
                <span className="quote-task-days">{formatDays(task.days)}</span>
              </label>
            ))}
          </div>

          <div className="total-bar">
            <div>
              <small className="mono">
                {selectedIds.length} / {tasks.length}
              </small>
              <span>{t("quote_total_days")}</span>
            </div>
            <strong>{formatDays(selectedDays)}</strong>
          </div>

          {error && <p className="auth-message">{error}</p>}

          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={handleBack} disabled={sending}>
              {t("quote_back")}
            </button>
            <button
              type="submit"
              className={`btn btn-grad ${sending ? "is-loading" : ""}`}
              disabled={sending || selectedIds.length === 0}
            >
              {sending ? t("order_sending") : t("quote_send")}
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="product-form-overlay" onClick={handleOverlayClick}>
      <form
        className="product-form order-modal quote-modal"
        onSubmit={handleAnalyze}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>
          {t("quote_title")}
          {serviceName}
        </h3>
        <p className="quote-hint">{t("quote_intro")}</p>

        <input
          type="text"
          placeholder={t("form_name")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={100}
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
          className="quote-description"
          placeholder={t("quote_description")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          minLength={MIN_DESCRIPTION}
          maxLength={MAX_DESCRIPTION}
          required
        />
        <p className="quote-counter mono">
          {description.length} / {MAX_DESCRIPTION}
          {t("quote_chars")}
        </p>

        {sending && <p className="quote-hint">{t("quote_wait")}</p>}
        {error && <p className="auth-message">{error}</p>}

        <div className="form-actions">
          <button type="button" className="btn btn-outline" onClick={onClose} disabled={sending}>
            {t("order_cancel")}
          </button>
          <button type="submit" className={`btn btn-grad ${sending ? "is-loading" : ""}`} disabled={sending}>
            {sending ? t("quote_analyzing") : t("quote_analyze")}
          </button>
        </div>
      </form>
    </div>
  );
}

export default QuoteModal;
