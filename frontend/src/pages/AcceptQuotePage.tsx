import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { isAxiosError } from "axios";
import api from "../api";
import { useLang } from "../i18n";
import type { Key } from "../i18n";

interface QuoteSummary {
  quote_number: string;
  client_name: string;
  language: string;
  tasks: { title: string; description: string; days: number }[];
  total_days: number;
  daily_rate: number;
  total_price: number;
}

type Problem = "invalid" | "expired" | "used" | "error";

const PROBLEM_TEXTS: Record<Problem, [Key, Key]> = {
  invalid: ["accept_invalid_title", "accept_invalid_text"],
  expired: ["accept_expired_title", "accept_expired_text"],
  used: ["accept_used_title", "accept_used_text"],
  error: ["accept_error_title", "accept_error_text"],
};

// The server answers 404 (not valid), 410 (expired) or 409 (already accepted).
const problemFrom = (error: unknown): Problem => {
  const status = isAxiosError(error) ? error.response?.status : undefined;
  if (status === 404 || status === 422) return "invalid";
  if (status === 410) return "expired";
  if (status === 409) return "used";
  return "error";
};

function AcceptQuotePage() {
  const { t, lang, setLang } = useLang();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [summary, setSummary] = useState<QuoteSummary | null>(null);
  const [problem, setProblem] = useState<Problem | null>(token ? null : "invalid");
  const [accepting, setAccepting] = useState(false);
  const [orderNumber, setOrderNumber] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let active = true;
    api
      .post<QuoteSummary>("/quotes/accept/preview", { token })
      .then((response) => {
        if (!active) return;
        setSummary(response.data);
        // Show the page in the language the client used for the quote
        if (response.data.language === "en" || response.data.language === "fr") {
          setLang(response.data.language);
        }
      })
      .catch((error) => active && setProblem(problemFrom(error)));
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const formatDays = (days: number) => {
    const singular = lang === "fr" ? days < 2 : days <= 1;
    return days.toLocaleString(lang) + (singular ? t("quote_day") : t("quote_days"));
  };
  const money = (value: number) => `$${value.toFixed(2)}`;

  const handleAccept = async () => {
    setAccepting(true);
    try {
      const response = await api.post("/quotes/accept", { token });
      setOrderNumber(response.data.order_number);
    } catch (error) {
      setProblem(problemFrom(error));
    } finally {
      setAccepting(false);
    }
  };

  if (problem) {
    const [title, text] = PROBLEM_TEXTS[problem];
    return (
      <AcceptFrame>
        <div className="auth-card accept-state">
          <div className={`status-icon ${problem === "used" ? "success" : "error"}`}>
            {problem === "used" ? "✓" : "!"}
          </div>
          <h2>{t(title)}</h2>
          <p className={problem === "used" ? "auth-success" : "auth-message"}>{t(text)}</p>
          <Link to="/" className="auth-cta">{t("accept_back")}</Link>
        </div>
      </AcceptFrame>
    );
  }

  if (orderNumber) {
    return (
      <AcceptFrame>
        <div className="auth-card accept-state">
          <div className="status-icon success">✓</div>
          <h2>{t("accept_done_title")}</h2>
          <p className="auth-success">
            {t("accept_done_text_1")}
            <strong className="mono">{orderNumber}</strong>
            {t("accept_done_text_2")}
          </p>
          <Link to="/" className="auth-cta">{t("accept_back")}</Link>
        </div>
      </AcceptFrame>
    );
  }

  if (!summary) {
    return (
      <AcceptFrame>
        <p className="status-text">{t("accept_loading")}</p>
      </AcceptFrame>
    );
  }

  return (
    <AcceptFrame>
      <h1 className="accept-headline">
        {t("accept_ready_1")}
        <span className="grad-text">{t("accept_ready_2")}</span>
      </h1>
      <h2 className="accept-number mono">
        {t("accept_title")}
        {summary.quote_number}
      </h2>

      <div className="auth-card accept-card">
        <p className="accept-intro">
          {t("accept_hello")}
          {summary.client_name}. {t("accept_intro")}
        </p>

        <div className="accept-task-list">
          {summary.tasks.map((task, index) => (
            <div className="accept-task" key={index}>
              <span className="accept-check" aria-hidden="true">
                <svg viewBox="0 0 16 16">
                  <path d="M3 8.5l3.2 3.2L13 4.8" />
                </svg>
              </span>
              <div className="accept-task-text">
                <strong>{task.title}</strong>
                <p>{task.description}</p>
              </div>
              <span className="quote-task-days">{formatDays(task.days)}</span>
            </div>
          ))}
        </div>

        <div className="total-bar accept-totals">
          <div>
            <small className="mono">
              {t("accept_total_days")}: {formatDays(summary.total_days)} · {t("accept_daily_rate")}:{" "}
              {money(summary.daily_rate)}
            </small>
            <span>{t("accept_total")}</span>
          </div>
          <strong>{money(summary.total_price)}</strong>
        </div>

        <p className="accept-note">{t("accept_note")}</p>
        <button
          type="button"
          className={`btn btn-grad btn-block accept-btn ${accepting ? "is-loading" : ""}`}
          onClick={handleAccept}
          disabled={accepting}
        >
          {accepting ? t("accept_accepting") : t("accept_button")}
        </button>
      </div>
    </AcceptFrame>
  );
}

// Centered logo tile and soft glows around every state of the page
function AcceptFrame({ children }: { children: ReactNode }) {
  return (
    <div className="accept-page">
      <Link to="/shop" className="logo-tile" aria-label="Cantek">
        <img src="/logo.png" alt="Cantek" />
      </Link>
      {children}
    </div>
  );
}

export default AcceptQuotePage;
