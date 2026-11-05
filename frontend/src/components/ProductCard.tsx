import ServiceIcon from "./ServiceIcon";
import { useLang } from "../i18n";

interface ProductCardProps {
  name: string;
  description: string | null;
  price: number;
  discountPercent: number;
  photoUrl: string | null;
  quoteOnly?: boolean;
  isLoggedIn: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onOrder?: () => void;
}

function ProductCard({
  name,
  description,
  price,
  discountPercent,
  photoUrl,
  quoteOnly = false,
  isLoggedIn,
  onEdit,
  onDelete,
  onOrder,
}: ProductCardProps) {
  const { t } = useLang();
  const hasDiscount = discountPercent > 0;
  const finalPrice = price - (price * discountPercent) / 100;

  return (
    <div className={`product-card ${quoteOnly && !isLoggedIn ? "featured" : ""}`}>
      <div className="service-chip">
        <ServiceIcon icon={photoUrl} />
      </div>
      <h3>{name}</h3>
      <p className="product-desc">{description}</p>

      <div className="product-bottom">
        {quoteOnly ? (
          <span className="new-price quote-price">
            {isLoggedIn ? "Price on quote" : t("quote_price_label")}
          </span>
        ) : hasDiscount ? (
          <div className="price-block">
            <span className="old-price">${price.toFixed(2)}</span>
            <span className="new-price">${finalPrice.toFixed(2)}</span>
            <span className="discount-badge">-{discountPercent}%</span>
          </div>
        ) : (
          <span className="new-price">${price.toFixed(2)}</span>
        )}

        {onOrder && !isLoggedIn && (
          <button
            className={`btn btn-sm order-btn ${quoteOnly ? "btn-grad" : "btn-ink"}`}
            onClick={onOrder}
          >
            {quoteOnly ? t("quote_button") : t("order_button")}
          </button>
        )}

        {isLoggedIn && (
          <div className="card-actions">
            <button className="btn btn-sm btn-ink edit-btn" onClick={onEdit}>Edit</button>
            <button className="btn btn-sm btn-outline delete-btn" onClick={onDelete}>Delete</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProductCard;