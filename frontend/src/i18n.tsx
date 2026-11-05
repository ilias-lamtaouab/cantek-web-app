import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

export type Lang = "en" | "fr";

const en = {
  nav_shop: "Shop",
  nav_admin: "Admin",
  nav_view_site: "View site",

  hero_title_1: "Software and AI, ",
  hero_title_2: "built around you",
  hero_sub:
    "Cantek designs custom web, mobile, and AI solutions — private, modular, and built to fit the way your team actually works.",
  loading_services: "Loading services...",
  services_title: "Services",
  order_button: "Order",

  nav_how: "How it works",
  nav_contact: "Contact",
  theme_to_dark: "Switch to night mode",
  theme_to_light: "Switch to day mode",
  hero_see_services: "See the services",
  hero_phone_title: "Your project, in tasks",
  hero_phone_hint: "Untick what you don't need.",
  hero_task_1: "Online menu",
  hero_task_2: "Table reservations",
  hero_task_3: "Admin page",
  hero_task_4: "Email confirmations",
  hero_task_5: "Online payments",
  hero_task_word: "task",
  hero_tasks_word: "tasks",
  hero_day_short: "d",
  hero_total: "Total",
  hero_send: "Send my selection",
  hero_sent: "Sent",
  hero_chip_service: "Custom Development",
  hero_chip_ai: "AI analysis",
  hero_chip_found: "4 tasks found",
  hero_chip_quote: "Quote CTK-Q-00008",
  hero_chip_accepted: "Accepted",

  how_title_1: "How ",
  how_title_2: "ordering works",
  how_sub: "Four simple steps, from your first click to your confirmation.",
  how_1_title: "Choose a service",
  how_1_text: "Browse our services and pick the one that fits your project.",
  how_2_title: "Send your order",
  how_2_text: "Enter your name and email, and tell us a little about your project.",
  how_3_title: "We confirm it",
  how_3_text: "The Cantek team reviews your order and confirms it.",
  how_4_title: "Get your PDF",
  how_4_text: "You receive a confirmation email with a PDF attached.",

  about_title_1: "Who ",
  about_title_2: "we are",
  about_text:
    "Cantek is a software and AI studio based in Montreal and Marrakech, building custom digital products for teams who need more than an off-the-shelf tool.",
  about_point_1: "Custom web, mobile, and AI solutions",
  about_point_2: "Private and secure by design",
  about_point_3: "Built around how your team works",
  stat_1_label: "Core service lines",
  stat_2_label: "Custom-built, no templates",
  stat_3_label: "Cities: Montreal and Marrakech",

  contact_title_1: "Let's ",
  contact_title_2: "talk",
  contact_sub: "Tell us about your project — we'll get back to you shortly.",
  contact_email_label: "Email",
  contact_based_label: "Based in",
  city: "Montreal & Marrakech",
  form_name: "Your name",
  form_email: "Your email",
  form_message: "Tell us about your project",
  form_send: "Send Message",
  form_sending: "Sending...",
  form_success: "Thanks! We'll be in touch soon.",
  form_error: "Something went wrong. Please try again.",

  footer_tagline: "Software and AI, built around you.",

  order_title: "Order: ",
  order_total: "Total: ",
  order_note: "Tell us about your project (optional)",
  order_cancel: "Cancel",
  order_send: "Send order",
  order_sending: "Sending...",
  order_sent_title: "Order sent",
  order_sent_text:
    "Thank you! You will receive a confirmation email with a PDF once the Cantek team confirms your order.",
  order_close: "Close",

  quote_price_label: "Price on quote",
  quote_button: "Request a quote",
  quote_title: "Request a quote: ",
  quote_intro:
    "Describe your project. Our AI assistant will split it into tasks with an estimated number of days.",
  quote_description: "Describe your project (at least 30 characters)",
  quote_chars: " characters",
  quote_analyze: "Analyse my project",
  quote_analyzing: "Analysing...",
  quote_wait: "This can take up to a minute. Please keep this window open.",
  quote_checklist_title: "Choose the tasks you need",
  quote_checklist_hint:
    "Untick the tasks you do not need. The final price is calculated by Cantek from the selected days.",
  quote_days: " days",
  quote_day: " day",
  quote_total_days: "Selected: ",
  quote_back: "Back",
  quote_send: "Send my request",
  quote_none_selected: "Please select at least one task.",
  quote_unavailable: "The project analysis is not available right now. Please try again later.",

  accept_loading: "Loading your quote...",
  accept_title: "Your quote ",
  accept_ready_1: "Your quote is ",
  accept_ready_2: "ready",
  accept_hello: "Hello ",
  accept_intro: "Here is the summary of your quote. Check it, then click the button to accept it.",
  accept_total_days: "Total days",
  accept_daily_rate: "Daily rate",
  accept_total: "Total",
  accept_button: "Accept the quote",
  accept_accepting: "Accepting...",
  accept_note:
    "When you accept, an order is created. The Cantek team will confirm it by email with a PDF.",
  accept_done_title: "Quote accepted",
  accept_done_text_1: "Thank you! Your order ",
  accept_done_text_2:
    " has been created. The Cantek team will confirm it by email with a PDF.",
  accept_invalid_title: "Link not valid",
  accept_invalid_text:
    "This link is not valid. Please check that you opened the full link from our email.",
  accept_expired_title: "Link expired",
  accept_expired_text: "This link has expired. Please contact us to get a new quote.",
  accept_used_title: "Quote already accepted",
  accept_used_text:
    "This quote has already been accepted. You will receive the order confirmation by email.",
  accept_error_title: "Not available",
  accept_error_text: "This page is not available right now. Please try again later.",
  accept_back: "Back to the site",
  quote_sent_title: "Quote request sent",
  quote_sent_text:
    "Thank you! The Cantek team will review your request and send you the quote by email.",
};

type Dict = typeof en;
export type Key = keyof Dict;

const fr: Dict = {
  nav_shop: "Boutique",
  nav_admin: "Admin",
  nav_view_site: "Voir le site",

  hero_title_1: "Logiciels et IA, ",
  hero_title_2: "pensés pour vous",
  hero_sub:
    "Cantek conçoit des solutions web, mobiles et d’IA sur mesure — privées, modulaires et adaptées à votre façon de travailler.",
  loading_services: "Chargement des services...",
  services_title: "Services",
  order_button: "Commander",

  nav_how: "Comment ça marche",
  nav_contact: "Contact",
  theme_to_dark: "Passer en mode nuit",
  theme_to_light: "Passer en mode jour",
  hero_see_services: "Voir les services",
  hero_phone_title: "Votre projet, en tâches",
  hero_phone_hint: "Décochez ce dont vous n’avez pas besoin.",
  hero_task_1: "Menu en ligne",
  hero_task_2: "Réservation de tables",
  hero_task_3: "Page d’administration",
  hero_task_4: "Confirmations par email",
  hero_task_5: "Paiement en ligne",
  hero_task_word: "tâche",
  hero_tasks_word: "tâches",
  hero_day_short: "j",
  hero_total: "Total",
  hero_send: "Envoyer ma sélection",
  hero_sent: "Envoyé",
  hero_chip_service: "Développement sur mesure",
  hero_chip_ai: "Analyse IA",
  hero_chip_found: "4 tâches trouvées",
  hero_chip_quote: "Devis CTK-Q-00008",
  hero_chip_accepted: "Accepté",

  how_title_1: "Comment ",
  how_title_2: "commander",
  how_sub: "Quatre étapes simples, de votre premier clic à votre confirmation.",
  how_1_title: "Choisissez un service",
  how_1_text: "Parcourez nos services et choisissez celui qui correspond à votre projet.",
  how_2_title: "Envoyez votre commande",
  how_2_text: "Indiquez votre nom et votre email, et parlez-nous un peu de votre projet.",
  how_3_title: "Nous la confirmons",
  how_3_text: "L’équipe Cantek examine votre commande et la confirme.",
  how_4_title: "Recevez votre PDF",
  how_4_text: "Vous recevez un email de confirmation avec un PDF en pièce jointe.",

  about_title_1: "Qui ",
  about_title_2: "nous sommes",
  about_text:
    "Cantek est un studio de logiciels et d’IA basé à Montréal et à Marrakech, qui crée des produits numériques sur mesure pour les équipes ayant besoin de plus qu’un outil prêt à l’emploi.",
  about_point_1: "Solutions web, mobiles et d’IA sur mesure",
  about_point_2: "Confidentialité et sécurité dès la conception",
  about_point_3: "Adapté à la façon de travailler de votre équipe",
  stat_1_label: "Domaines d’expertise",
  stat_2_label: "Sur mesure, sans solution toute faite",
  stat_3_label: "Villes : Montréal et Marrakech",

  contact_title_1: "Contactez-",
  contact_title_2: "nous",
  contact_sub: "Parlez-nous de votre projet — nous vous répondrons rapidement.",
  contact_email_label: "Email",
  contact_based_label: "Basés à",
  city: "Montréal et Marrakech",
  form_name: "Votre nom",
  form_email: "Votre email",
  form_message: "Parlez-nous de votre projet",
  form_send: "Envoyer le message",
  form_sending: "Envoi...",
  form_success: "Merci ! Nous vous recontacterons bientôt.",
  form_error: "Une erreur s’est produite. Veuillez réessayer.",

  footer_tagline: "Logiciels et IA, pensés pour vous.",

  order_title: "Commande : ",
  order_total: "Total : ",
  order_note: "Parlez-nous de votre projet (facultatif)",
  order_cancel: "Annuler",
  order_send: "Envoyer la commande",
  order_sending: "Envoi...",
  order_sent_title: "Commande envoyée",
  order_sent_text:
    "Merci ! Vous recevrez un email de confirmation avec un PDF dès que l’équipe Cantek aura confirmé votre commande.",
  order_close: "Fermer",

  quote_price_label: "Prix sur devis",
  quote_button: "Demander un devis",
  quote_title: "Demande de devis : ",
  quote_intro:
    "Décrivez votre projet. Notre assistant IA le découpe en tâches avec un nombre de jours estimé.",
  quote_description: "Décrivez votre projet (au moins 30 caractères)",
  quote_chars: " caractères",
  quote_analyze: "Analyser mon projet",
  quote_analyzing: "Analyse en cours...",
  quote_wait: "Cela peut prendre jusqu’à une minute. Veuillez garder cette fenêtre ouverte.",
  quote_checklist_title: "Choisissez les tâches dont vous avez besoin",
  quote_checklist_hint:
    "Décochez les tâches dont vous n’avez pas besoin. Le prix final est calculé par Cantek à partir des jours choisis.",
  quote_days: " jours",
  quote_day: " jour",
  quote_total_days: "Sélection : ",
  quote_back: "Retour",
  quote_send: "Envoyer ma demande",
  quote_none_selected: "Veuillez choisir au moins une tâche.",
  quote_unavailable: "L’analyse du projet n’est pas disponible pour le moment. Veuillez réessayer plus tard.",

  accept_loading: "Chargement de votre devis...",
  accept_title: "Votre devis ",
  accept_ready_1: "Votre devis est ",
  accept_ready_2: "prêt",
  accept_hello: "Bonjour ",
  accept_intro: "Voici le résumé de votre devis. Vérifiez-le, puis cliquez sur le bouton pour l’accepter.",
  accept_total_days: "Nombre total de jours",
  accept_daily_rate: "Tarif journalier",
  accept_total: "Total",
  accept_button: "Accepter le devis",
  accept_accepting: "Acceptation...",
  accept_note:
    "En acceptant, une commande est créée. L’équipe Cantek la confirmera par email avec un PDF.",
  accept_done_title: "Devis accepté",
  accept_done_text_1: "Merci ! Votre commande ",
  accept_done_text_2:
    " a été créée. L’équipe Cantek la confirmera par email avec un PDF.",
  accept_invalid_title: "Lien non valide",
  accept_invalid_text:
    "Ce lien n’est pas valide. Vérifiez que vous avez ouvert le lien complet de notre email.",
  accept_expired_title: "Lien expiré",
  accept_expired_text: "Ce lien a expiré. Contactez-nous pour obtenir un nouveau devis.",
  accept_used_title: "Devis déjà accepté",
  accept_used_text:
    "Ce devis a déjà été accepté. Vous recevrez la confirmation de commande par email.",
  accept_error_title: "Indisponible",
  accept_error_text: "Cette page n’est pas disponible pour le moment. Veuillez réessayer plus tard.",
  accept_back: "Retour au site",
  quote_sent_title: "Demande de devis envoyée",
  quote_sent_text:
    "Merci ! L’équipe Cantek va étudier votre demande et vous enverra le devis par email.",
};

const dictionaries: Record<Lang, Dict> = { en, fr };

interface LangContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: Key) => string;
}

const LangContext = createContext<LangContextValue | null>(null);

function getInitialLang(): Lang {
  try {
    const saved = localStorage.getItem("lang");
    if (saved === "en" || saved === "fr") return saved;
  } catch (error) {
    console.error("Could not read language:", error);
  }
  return navigator.language.toLowerCase().startsWith("fr") ? "fr" : "en";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getInitialLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = (newLang: Lang) => {
    setLangState(newLang);
    try {
      localStorage.setItem("lang", newLang);
    } catch (error) {
      console.error("Could not save language:", error);
    }
  };

  const t = (key: Key) => dictionaries[lang][key];

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

// The hook lives next to its provider on purpose (one i18n file).
// eslint-disable-next-line react-refresh/only-export-components
export function useLang() {
  const context = useContext(LangContext);
  if (!context) {
    throw new Error("useLang must be used inside LanguageProvider");
  }
  return context;
}