import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import api from "../api";

export interface QuoteTask {
  id: number;
  title: string;
  description: string;
  days: number;
}

export interface Quote {
  id: number;
  client_name: string;
  client_email: string;
  description: string;
  language: string;
  status: string;
  daily_rate: number | null;
  total_days: number | null;
  total_price: number | null;
  created_at: string;
  submitted_at: string | null;
  sent_at: string | null;
  accepted_at: string | null;
  order_id: number | null;
  tasks: QuoteTask[];
}

interface QuotesPanelProps {
  quotes: Quote[];
  token: string;
  onQuotesChanged: () => void;
  onShowOrder: (orderId: number) => void;
}

const quoteNumber = (id: number) => `CTK-Q-${String(id).padStart(5, "0")}`;
const orderNumber = (id: number) => `CTK-${String(id).padStart(5, "0")}`;

const STATUS_LABELS: Record<string, { badge: string; label: string }> = {
  pending: { badge: "pending", label: "Pending" },
  sent: { badge: "confirmed", label: "Sent" },
  accepted: { badge: "accepted", label: "Accepted" },
};
const money = (value: number | null) => `$${(value ?? 0).toFixed(2)}`;

const errorText = (error: unknown, fallback: string) => {
  const detail = isAxiosError(error) ? error.response?.data?.detail : null;
  return typeof detail === "string" ? detail : fallback;
};

function QuotesPanel({ quotes, token, onQuotesChanged, onShowOrder }: QuotesPanelProps) {
  const headers = { Authorization: `Bearer ${token}` };

  // Default daily rate used for new quotes
  const [defaultRate, setDefaultRate] = useState("");
  const [rateIsDefault, setRateIsDefault] = useState(false);
  const [savingRate, setSavingRate] = useState(false);
  const [rateMessage, setRateMessage] = useState<{ ok: boolean; text: string } | null>(null);

  // The quote that is open, and the values typed in its fields
  const [openId, setOpenId] = useState<number | null>(null);
  const [editRate, setEditRate] = useState("");
  const [editDays, setEditDays] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);
  const [quoteError, setQuoteError] = useState<{ id: number; text: string } | null>(null);

  useEffect(() => {
    api
      .get("/settings/daily-rate", { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => {
        setDefaultRate(String(response.data.daily_rate));
        setRateIsDefault(response.data.is_default);
      })
      .catch((error) => console.error("Failed to fetch daily rate:", error));
  }, [token]);

  const handleSaveDefaultRate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingRate(true);
    setRateMessage(null);
    try {
      const response = await api.put(
        "/settings/daily-rate",
        { daily_rate: parseFloat(defaultRate) },
        { headers }
      );
      setDefaultRate(String(response.data.daily_rate));
      setRateIsDefault(false);
      setRateMessage({ ok: true, text: "Saved. New quotes will use this rate." });
    } catch (error) {
      setRateMessage({ ok: false, text: errorText(error, "Could not save the rate. Please check the value.") });
    } finally {
      setSavingRate(false);
    }
  };

  const openQuote = (quote: Quote) => {
    if (openId === quote.id) {
      setOpenId(null);
      return;
    }
    setOpenId(quote.id);
    setQuoteError(null);
    setEditRate(String(quote.daily_rate ?? ""));
    setEditDays(Object.fromEntries(quote.tasks.map((task) => [task.id, String(task.days)])));
  };

  const hasChanges = (quote: Quote) =>
    parseFloat(editRate) !== quote.daily_rate ||
    quote.tasks.some((task) => parseFloat(editDays[task.id]) !== task.days);

  const handleSave = async (quote: Quote) => {
    setBusyId(quote.id);
    setQuoteError(null);
    try {
      const response = await api.put<Quote>(
        `/quotes/${quote.id}`,
        {
          daily_rate: parseFloat(editRate),
          tasks: quote.tasks.map((task) => ({ id: task.id, days: parseFloat(editDays[task.id]) })),
        },
        { headers }
      );
      setEditRate(String(response.data.daily_rate));
      setEditDays(Object.fromEntries(response.data.tasks.map((task) => [task.id, String(task.days)])));
      onQuotesChanged();
    } catch (error) {
      setQuoteError({
        id: quote.id,
        text: errorText(error, "Could not save. Days must be between 0.5 and 60, in steps of 0.5, and the rate above 0."),
      });
    } finally {
      setBusyId(null);
    }
  };

  const handleSend = async (quote: Quote) => {
    const confirmed = window.confirm(
      `Send this quote (${money(quote.total_price)}) to ${quote.client_email} by email?`
    );
    if (!confirmed) return;

    setBusyId(quote.id);
    setQuoteError(null);
    try {
      await api.post(`/quotes/${quote.id}/send`, {}, { headers });
      onQuotesChanged();
    } catch (error) {
      setQuoteError({ id: quote.id, text: errorText(error, "Could not send the quote. Please try again.") });
    } finally {
      setBusyId(null);
    }
  };

  const selected = quotes.find((quote) => quote.id === openId) || null;

  return (
    <div className="messages-panel quotes-panel">
      <h3>Quotes</h3>

      <form className="message-card rate-card" onSubmit={handleSaveDefaultRate}>
        <label htmlFor="default-rate">
          <strong>Daily rate for new quotes ($)</strong>
          {rateIsDefault && <span className="order-date"> · example value, not set yet</span>}
        </label>
        <div className="rate-row">
          <input
            id="default-rate"
            type="number"
            min="1"
            step="0.01"
            value={defaultRate}
            onChange={(e) => setDefaultRate(e.target.value)}
            required
          />
          <button type="submit" className="btn btn-ink btn-sm reply-btn" disabled={savingRate}>
            {savingRate ? "Saving..." : "Save rate"}
          </button>
        </div>
        {rateMessage && (
          <p className={rateMessage.ok ? "rate-saved" : "order-error"}>{rateMessage.text}</p>
        )}
      </form>

      {quotes.length === 0 ? (
        <p className="status-text">No quote requests yet.</p>
      ) : (
        <div className="quotes-layout">
          <ul className="quote-list">
            {quotes.map((quote) => {
              const status = STATUS_LABELS[quote.status] || STATUS_LABELS.sent;
              const isOpen = openId === quote.id;
              return (
                <li key={quote.id}>
                  <button
                    type="button"
                    className={`quote-item ${isOpen ? "active" : ""}`}
                    onClick={() => openQuote(quote)}
                    aria-expanded={isOpen}
                  >
                    <span className="quote-item-row">
                      <span className="mono quote-id">{quoteNumber(quote.id)}</span>
                      <span className={`status-badge ${status.badge}`}>{status.label}</span>
                    </span>
                    <span className="quote-item-row">
                      <strong>{quote.client_name}</strong>
                      <span className="quote-item-total">{money(quote.total_price)}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="quote-detail-col">
            {selected ? (
              <QuoteDetail
                quote={selected}
                isBusy={busyId === selected.id}
                editDays={editDays}
                editRate={editRate}
                error={quoteError && quoteError.id === selected.id ? quoteError.text : null}
                hasChanges={hasChanges(selected)}
                onDaysChange={(taskId, value) => setEditDays((prev) => ({ ...prev, [taskId]: value }))}
                onRateChange={setEditRate}
                onClose={() => openQuote(selected)}
                onSave={() => handleSave(selected)}
                onSend={() => handleSend(selected)}
                onShowOrder={onShowOrder}
              />
            ) : (
              <p className="quote-detail-empty">Select a quote to see its tasks.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface QuoteDetailProps {
  quote: Quote;
  isBusy: boolean;
  editDays: Record<number, string>;
  editRate: string;
  error: string | null;
  hasChanges: boolean;
  onDaysChange: (taskId: number, value: string) => void;
  onRateChange: (value: string) => void;
  onClose: () => void;
  onSave: () => void;
  onSend: () => void;
  onShowOrder: (orderId: number) => void;
}

// Detail card of the selected quote (right column)
function QuoteDetail({
  quote,
  isBusy,
  editDays,
  editRate,
  error,
  hasChanges,
  onDaysChange,
  onRateChange,
  onClose,
  onSave,
  onSend,
  onShowOrder,
}: QuoteDetailProps) {
  const isPending = quote.status === "pending";
  const status = STATUS_LABELS[quote.status] || STATUS_LABELS.sent;

  return (
    <div className="message-card quote-detail">
      <div className="order-card-head">
        <div>
          <p className="mono quote-id">
            {quoteNumber(quote.id)} · {quote.language.toUpperCase()}
          </p>
          <h4>{quote.client_name}</h4>
          <p className="order-client">{quote.client_email}</p>
        </div>
        <span className={`status-badge ${status.badge}`}>{status.label}</span>
      </div>

      <div className="quote-details">
        <p className="quote-label">Client's project</p>
        <p className="quote-project">{quote.description}</p>

        <p className="quote-label">Selected tasks</p>
        {quote.tasks.map((task) => (
          <div className="quote-admin-task" key={task.id}>
            <div>
              <strong>{task.title}</strong>
              <p>{task.description}</p>
            </div>
            {isPending ? (
              <label className="quote-days-input">
                <input
                  type="number"
                  min="0.5"
                  max="60"
                  step="0.5"
                  value={editDays[task.id] ?? ""}
                  onChange={(e) => onDaysChange(task.id, e.target.value)}
                />
                days
              </label>
            ) : (
              <span className="quote-task-days">{task.days} days</span>
            )}
          </div>
        ))}

        {isPending && (
          <label className="quote-rate-input">
            Daily rate for this quote ($)
            <input
              type="number"
              min="1"
              step="0.01"
              value={editRate}
              onChange={(e) => onRateChange(e.target.value)}
            />
          </label>
        )}
        {isPending && hasChanges && (
          <p className="order-date">Save your changes to recalculate the total before sending.</p>
        )}
      </div>

      <div className="total-bar">
        <small className="mono">
          {quote.total_days} days × {money(quote.daily_rate)} =
        </small>
        <strong>{money(quote.total_price)}</strong>
      </div>

      <div className="order-actions">
        <span className="order-date">
          {quote.accepted_at
            ? `Accepted ${new Date(quote.accepted_at + "Z").toLocaleString()}`
            : quote.sent_at
            ? `Sent ${new Date(quote.sent_at + "Z").toLocaleString()}`
            : `Requested ${new Date((quote.submitted_at || quote.created_at) + "Z").toLocaleString()}`}
        </span>
        <div className="quote-actions">
          {quote.order_id !== null && (
            <button
              className="btn btn-outline btn-sm quote-open-btn"
              onClick={() => onShowOrder(quote.order_id as number)}
            >
              Order {orderNumber(quote.order_id)}
            </button>
          )}
          <button className="btn btn-outline btn-sm quote-open-btn" onClick={onClose}>
            Close
          </button>
          {isPending && (
            <>
              <button
                className="btn btn-ink btn-sm reply-btn"
                onClick={onSave}
                disabled={isBusy || !hasChanges}
              >
                Save changes
              </button>
              <button
                className="btn btn-grad btn-sm confirm-btn"
                onClick={onSend}
                disabled={isBusy || hasChanges}
              >
                {isBusy ? "Please wait..." : "Send quote"}
              </button>
            </>
          )}
        </div>
      </div>
      {error && <p className="order-error">{error}</p>}
    </div>
  );
}

export default QuotesPanel;
