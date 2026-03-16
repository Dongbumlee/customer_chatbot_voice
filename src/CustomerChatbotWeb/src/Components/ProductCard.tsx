import type { Product } from "../types";

interface ProductCardProps {
  product: Product;
}

/**
 * Product card — renders product information returned by the Product Agent.
 * Displays image, name, price, description, and category.
 */
export function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="product-card">
      {product.image_url && (
        <img
          src={product.image_url}
          alt={product.name}
          className="product-card__image"
          loading="lazy"
        />
      )}
      <div className="product-card__body">
        <h3 className="product-card__name">{product.name}</h3>
        <span className="product-card__category">{product.category}</span>
        <p className="product-card__price">${product.price.toFixed(2)}</p>
        <p className="product-card__description">{product.description}</p>
      </div>
    </div>
  );
}
