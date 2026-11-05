import { useLang } from "../i18n";

function HowItWorks() {
  const { t } = useLang();

  const steps = [
    { title: t("how_1_title"), text: t("how_1_text") },
    { title: t("how_2_title"), text: t("how_2_text") },
    { title: t("how_3_title"), text: t("how_3_text") },
    { title: t("how_4_title"), text: t("how_4_text") },
  ];

  return (
    <section className="how-section container" id="how">
      <h2 className="section-title">
        {t("how_title_1")}
        <span className="grad-text">{t("how_title_2")}</span>
      </h2>
      <p className="how-sub">{t("how_sub")}</p>

      <ol className="how-timeline">
        {steps.map((step, index) => (
          <li className="how-step reveal" key={index}>
            <span className="how-dot" aria-hidden="true">{index + 1}</span>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default HowItWorks;
