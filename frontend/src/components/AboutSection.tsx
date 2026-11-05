import { useLang } from "../i18n";

function AboutSection() {
  const { t } = useLang();

  return (
    <section className="about-section container">
      <div className="about-text">
        <h2 className="section-title">
          {t("about_title_1")}
          <span className="grad-text">{t("about_title_2")}</span>
        </h2>
        <p>{t("about_text")}</p>

        <ul className="about-points">
          <li>{t("about_point_1")}</li>
          <li>{t("about_point_2")}</li>
          <li>{t("about_point_3")}</li>
        </ul>
      </div>

      <div className="stats-grid">
        <div className="stat">
          <h3 className="grad-text">3</h3>
          <p>{t("stat_1_label")}</p>
        </div>
        <div className="stat">
          <h3 className="grad-text">100%</h3>
          <p>{t("stat_2_label")}</p>
        </div>
        <div className="stat">
          <h3 className="grad-text">2</h3>
          <p>{t("stat_3_label")}</p>
        </div>
      </div>
    </section>
  );
}

export default AboutSection;