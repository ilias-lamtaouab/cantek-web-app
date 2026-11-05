import { Link, useLocation, useNavigate } from "react-router-dom";
import { useLang } from "../i18n";
import ThemeToggle from "./ThemeToggle";

function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { lang, setLang, t } = useLang();
  const onShop = location.pathname === "/shop" || location.pathname === "/";
  const onAdmin = location.pathname === "/admin";
  const isLoggedIn = !!localStorage.getItem("token");

  const scrollToSection = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    if (!onShop) navigate("/shop");
    setTimeout(
      () => {
        document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
      },
      onShop ? 0 : 400
    );
  };

  const scrollToTop = (e: React.MouseEvent) => {
    if (onShop) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  // The admin has its own sidebar, and the accept page its own centered logo.
  if (onAdmin || location.pathname === "/accept-quote") return null;

  return (
    <header className="site-header">
      <div className="container header-inner">
        <Link to="/shop" onClick={scrollToTop} className="logo-tile" aria-label="Cantek">
          <img src="/logo.png" alt="Cantek" />
        </Link>

        <nav className="header-nav" aria-label="Main">
          <a href="/shop#services" className="nav-link" onClick={scrollToSection("services")}>
            {t("nav_shop")}
          </a>
          <a href="/shop#how" className="nav-link nav-extra" onClick={scrollToSection("how")}>
            {t("nav_how")}
          </a>
          <a href="/shop#contact" className="nav-link nav-extra" onClick={scrollToSection("contact")}>
            {t("nav_contact")}
          </a>
          {isLoggedIn && (
            <Link to="/admin" className="nav-link">{t("nav_admin")}</Link>
          )}

          <div className="lang-switch" role="group" aria-label="Language">
            <button
              className={`lang-btn ${lang === "en" ? "active" : ""}`}
              onClick={() => setLang("en")}
              aria-pressed={lang === "en"}
            >
              EN
            </button>
            <button
              className={`lang-btn ${lang === "fr" ? "active" : ""}`}
              onClick={() => setLang("fr")}
              aria-pressed={lang === "fr"}
            >
              FR
            </button>
          </div>

          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

export default TopBar;
