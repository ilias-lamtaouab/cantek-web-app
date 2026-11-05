import { useState } from "react";
import { useLang } from "../i18n";

type Theme = "light" | "dark";

const STORAGE_KEY = "theme";

// The theme is set on <html> (also by the small script in index.html before React loads).
const currentTheme = (): Theme =>
  document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";

function applyTheme(theme: Theme) {
  const root = document.documentElement;

  // Short color transition while switching, unless the visitor prefers reduced motion.
  if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    root.classList.add("theme-switching");
    window.setTimeout(() => root.classList.remove("theme-switching"), 400);
  }

  if (theme === "dark") root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");

  try {
    if (theme === "dark") localStorage.setItem(STORAGE_KEY, "dark");
    else localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error("Could not save theme:", error);
  }
}

function ThemeToggle() {
  const { t } = useLang();
  const [theme, setTheme] = useState<Theme>(currentTheme);
  const label = theme === "dark" ? t("theme_to_light") : t("theme_to_dark");

  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
  };

  return (
    <button type="button" className="theme-toggle" onClick={toggle} aria-label={label} title={label}>
      {theme === "dark" ? (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="4.5" />
          <path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z" />
        </svg>
      )}
    </button>
  );
}

export default ThemeToggle;
