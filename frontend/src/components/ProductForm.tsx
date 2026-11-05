import { useState } from "react";

interface ProductFormData {
  name: string;
  description: string;
  price: number;
  discount_percent: number;
  photo_url: string;
  name_fr?: string;
  description_fr?: string;
  quote_only: boolean;
}

interface ProductFormProps {
  initialData?: ProductFormData;
  onSubmit: (data: ProductFormData) => void;
  onCancel: () => void;
}

function ProductForm({ initialData, onSubmit, onCancel }: ProductFormProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [nameFr, setNameFr] = useState(initialData?.name_fr || "");
  const [descriptionFr, setDescriptionFr] = useState(initialData?.description_fr || "");
  const [price, setPrice] = useState(initialData?.price?.toString() || "");
  const [discountPercent, setDiscountPercent] = useState(
    initialData?.discount_percent?.toString() || "0"
  );
  const [photoUrl, setPhotoUrl] = useState(initialData?.photo_url || "");
  const [quoteOnly, setQuoteOnly] = useState(initialData?.quote_only || false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      description,
      name_fr: nameFr,
      description_fr: descriptionFr,
      price: price === "" ? 0 : parseFloat(price),
      discount_percent: parseFloat(discountPercent),
      photo_url: photoUrl,
      quote_only: quoteOnly,
    });
  };

  return (
    <div className="product-form-overlay">
      <form className="product-form" onSubmit={handleSubmit}>
        <h3>{initialData ? "Edit Service" : "Add New Service"}</h3>

        <input
          placeholder="Name (English)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <textarea
          placeholder="Description (English)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <input
          placeholder="Name (French)"
          value={nameFr}
          onChange={(e) => setNameFr(e.target.value)}
        />
        <textarea
          placeholder="Description (French)"
          value={descriptionFr}
          onChange={(e) => setDescriptionFr(e.target.value)}
        />
        <input
          type="number"
          step="0.01"
          placeholder={quoteOnly ? "Price (not used for quotes)" : "Price"}
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          required={!quoteOnly}
        />
        <input
          type="number"
          step="1"
          placeholder="Discount %"
          value={discountPercent}
          onChange={(e) => setDiscountPercent(e.target.value)}
        />
        <input
          placeholder="Photo URL (optional)"
          value={photoUrl}
          onChange={(e) => setPhotoUrl(e.target.value)}
        />
        <label className="form-checkbox">
          <input
            type="checkbox"
            className="check"
            checked={quoteOnly}
            onChange={(e) => setQuoteOnly(e.target.checked)}
          />
          Quote only (the client describes the project and gets an AI task list instead of a fixed price)
        </label>

        <div className="form-actions">
          <button type="submit" className="btn btn-grad">Save</button>
          <button type="button" className="btn btn-outline" onClick={onCancel}>Cancel</button>
        </div>
      </form>
    </div>
  );
}

export default ProductForm;