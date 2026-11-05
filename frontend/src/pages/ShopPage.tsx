import { useEffect, useRef, useState } from "react";
import ProductCard from "../components/ProductCard";
import HowItWorks from "../components/HowItWorks";
import AboutSection from "../components/AboutSection";
import ContactForm from "../components/ContactForm";
import Footer from "../components/Footer";
import OrderModal from "../components/OrderModal";
import QuoteModal from "../components/QuoteModal";
import HeroVisual from "../components/HeroVisual";
import { useLang } from "../i18n";
import api from "../api";

interface Product {
  id: number;
  name: string;
  description: string | null;
  price: number;
  discount_percent: number;
  photo_url: string | null;
  name_fr: string | null;
  description_fr: string | null;
  quote_only: boolean;
}

function ShopPage() {
  const { t, lang } = useLang();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);

  const localName = (product: Product) =>
    lang === "fr" && product.name_fr ? product.name_fr : product.name;

  const localDescription = (product: Product) =>
    lang === "fr" && product.description_fr
      ? product.description_fr
      : product.description;

  // Quote-only services go in the middle of the row; the others keep their order around them.
  const otherProducts = products.filter((product) => !product.quote_only);
  const middle = Math.floor(otherProducts.length / 2);
  const displayedProducts = [
    ...otherProducts.slice(0, middle),
    ...products.filter((product) => product.quote_only),
    ...otherProducts.slice(middle),
  ];

  useEffect(() => {
    api
      .get<Product[]>("/products")
      .then((response) => setProducts(response.data))
      .catch((error) => console.error("Failed to fetch products:", error))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (loading) return;

    const revealEls = Array.from(document.querySelectorAll<HTMLElement>(".reveal"));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            observer.unobserve(entry.target);
            const el = entry.target as HTMLElement;
            requestAnimationFrame(() => {
              requestAnimationFrame(() => {
                el.classList.add("visible");
              });
            });
          }
        });
      },
      { threshold: 0.15 }
    );

    revealEls.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [loading]);

  const scrollToServices = () =>
    document.getElementById("services")?.scrollIntoView({ behavior: "smooth", block: "start" });

  // "Request a quote" in the hero opens the quote form of the quote-only service.
  const requestQuote = () => {
    const quoteProduct = products.find((product) => product.quote_only);
    if (quoteProduct) setSelectedProduct(quoteProduct);
    else scrollToServices();
  };

  return (
    <div className="shop-page">
      <section className="hero">
        <div className="hero-glow g1" aria-hidden="true" />
        <div className="hero-glow g2" aria-hidden="true" />
        <div className="hero-grain" aria-hidden="true" />

        <div className="container hero-inner">
          <h1 className="hero-title">
            {t("hero_title_1")}
            <br />
            <span className="grad-text">{t("hero_title_2")}</span>
          </h1>
          <p className="hero-sub">{t("hero_sub")}</p>

          <HeroVisual />

          <div className="hero-cta">
            <button type="button" className="hero-cta-quote" onClick={requestQuote}>
              {t("quote_button")} <span aria-hidden="true">↓</span>
            </button>
            <button type="button" className="hero-cta-services" onClick={scrollToServices}>
              {t("hero_see_services")} <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </section>

      <section id="services" className="services-section container">
        <h2 className="section-title">{t("services_title")}</h2>
        {loading ? (
          <p className="status-text">{t("loading_services")}</p>
        ) : (
          <div className="product-grid" ref={gridRef}>
            {displayedProducts.map((product) => (
              <div className="reveal" key={product.id}>
                <ProductCard
                  name={localName(product)}
                  description={localDescription(product)}
                  price={product.price}
                  discountPercent={product.discount_percent}
                  photoUrl={product.photo_url}
                  quoteOnly={product.quote_only}
                  isLoggedIn={false}
                  onEdit={() => {}}
                  onDelete={() => {}}
                  onOrder={() => setSelectedProduct(product)}
                />
              </div>
            ))}
          </div>
        )}
      </section>

      <HowItWorks />
      <AboutSection />
      <ContactForm />
      <Footer />

      {selectedProduct && selectedProduct.quote_only && (
        <QuoteModal
          serviceName={localName(selectedProduct)}
          onClose={() => setSelectedProduct(null)}
        />
      )}

      {selectedProduct && !selectedProduct.quote_only && (
        <OrderModal
          product={{
            id: selectedProduct.id,
            name: localName(selectedProduct),
            price: selectedProduct.price,
            discount_percent: selectedProduct.discount_percent,
          }}
          onClose={() => setSelectedProduct(null)}
        />
      )}
    </div>
  );
}

export default ShopPage;