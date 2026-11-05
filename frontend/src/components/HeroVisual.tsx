import { useEffect, useState } from "react";
import { useLang } from "../i18n";
import type { Key } from "../i18n";

// Decorative demo of the quote flow shown in the hero (hidden from screen readers).
const TASKS: { label: Key; days: number }[] = [
  { label: "hero_task_1", days: 1.5 },
  { label: "hero_task_2", days: 2 },
  { label: "hero_task_3", days: 1 },
  { label: "hero_task_4", days: 1 },
  { label: "hero_task_5", days: 2 },
];
const DAILY_RATE = 400;
const TICKED_TASKS = 4;
const FINAL_DAYS = TASKS.slice(0, TICKED_TASKS).reduce((sum, task) => sum + task.days, 0);

type SendState = "idle" | "pulse" | "sent";

const reducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function Sparkle({ className }: { className: string }) {
  return (
    <svg className={`hero-star ${className}`} viewBox="0 0 40 40">
      <path d="M20 0C21 12 28 19 40 20 28 21 21 28 20 40 19 28 12 21 0 20 12 19 19 12 20 0Z" />
    </svg>
  );
}

function HeroVisual() {
  const { t, lang } = useLang();
  const [still] = useState(reducedMotion);
  const [ticked, setTicked] = useState(still ? TICKED_TASKS : 0);
  const [chips, setChips] = useState(still ? [true, true, true] : [false, false, false]);
  const [send, setSend] = useState<SendState>("idle");
  const [total, setTotal] = useState(still ? FINAL_DAYS * DAILY_RATE : 0);

  useEffect(() => {
    if (still) return;

    let cancelled = false;
    const timers: number[] = [];
    let frame = 0;
    let shown = 0;

    const wait = (ms: number) =>
      new Promise<void>((resolve) => {
        timers.push(window.setTimeout(resolve, ms));
      });

    // Count the total up with an ease-out, like the reference animation.
    const countTo = (target: number) => {
      cancelAnimationFrame(frame);
      const from = shown;
      const start = performance.now();
      const step = (now: number) => {
        const progress = Math.min(1, (now - start) / 450);
        shown = Math.round(from + (target - from) * (1 - Math.pow(1 - progress, 3)));
        setTotal(shown);
        if (progress < 1) frame = requestAnimationFrame(step);
      };
      frame = requestAnimationFrame(step);
    };

    const run = async () => {
      while (!cancelled) {
        cancelAnimationFrame(frame);
        shown = 0;
        setTicked(0);
        setChips([false, false, false]);
        setSend("idle");
        setTotal(0);

        await wait(900);
        setChips([true, false, false]);
        await wait(700);
        setChips([true, true, false]);
        await wait(600);

        let days = 0;
        for (let i = 0; i < TICKED_TASKS; i++) {
          setTicked(i + 1);
          days += TASKS[i].days;
          countTo(days * DAILY_RATE);
          await wait(850);
        }

        await wait(500);
        setSend("pulse");
        await wait(1000);
        setSend("sent");
        await wait(600);
        setChips([true, true, true]);
        await wait(4200);
      }
    };

    run();
    return () => {
      cancelled = true;
      timers.forEach((timer) => window.clearTimeout(timer));
      cancelAnimationFrame(frame);
    };
  }, [still]);

  const tickedDays = TASKS.slice(0, ticked).reduce((sum, task) => sum + task.days, 0);
  const days = (value: number) => value.toLocaleString(lang);

  return (
    <div className="hero-stage" aria-hidden="true">
      <Sparkle className="s1" />
      <Sparkle className="s2" />

      <div className={`hero-chip c1 ${chips[0] ? "show" : ""}`}>
        <small>{t("quote_price_label")}</small>
        {t("hero_chip_service")}
      </div>
      <div className={`hero-chip c3 ${chips[1] ? "show" : ""}`}>
        <small>{t("hero_chip_ai")}</small>
        {t("hero_chip_found")}
      </div>
      <div className={`hero-chip c2 ${chips[2] ? "show" : ""}`}>
        <small>{t("hero_chip_quote")}</small>
        {t("hero_chip_accepted")} · $2,200.00
      </div>

      <div className="phone">
        <div className="phone-screen">
          <div className="phone-title">{t("hero_phone_title")}</div>
          <p className="phone-hint">{t("hero_phone_hint")}</p>

          {TASKS.map((task, index) => (
            <div className={`phone-task ${index < ticked ? "on" : ""}`} key={task.label}>
              <i>
                <svg viewBox="0 0 16 16">
                  <path d="M3 8.5l3.2 3.2L13 4.8" />
                </svg>
              </i>
              {t(task.label)}
              <em>
                {days(task.days)} {t("hero_day_short")}
              </em>
            </div>
          ))}

          <div className="phone-total">
            <div>
              <small>
                {ticked} {ticked === 1 ? t("hero_task_word") : t("hero_tasks_word")} · {days(tickedDays)}{" "}
                {t("hero_day_short")}
              </small>
              {t("hero_total")}
            </div>
            <b>${total.toLocaleString("en-US")}</b>
          </div>

          <div className={`phone-send ${send === "pulse" ? "pulse" : ""} ${send === "sent" ? "pulse sent" : ""}`}>
            <span className="label-a">{t("hero_send")}</span>
            <span className="label-b">{t("hero_sent")} ✓</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HeroVisual;
