import { useLang } from "../i18n";

function Footer() {
  const { t } = useLang();

  return (
    <footer className="site-footer">
      <div className="container footer-inner">
        <div>
          <h3>Cantek</h3>
          <p>{t("footer_tagline")}</p>
        </div>
        <div className="footer-contact mono">
          <p>cantek.contact@gmail.com</p>
          <p>{t("city")}</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
