import type { Product } from "../lib/types";
import { money } from "../lib/money";

export function ProductDetails({
  product,
  onClose,
}: {
  product: Product;
  onClose(): void;
}) {
  return (
    <section aria-label="Карточка товара">
      <h2>{product.name}</h2>
      <img
        src={`/api/products/${product.id}/image`}
        alt={product.name}
        width={320}
        height={240}
      />
      <p>Товар №{product.id}</p>
      <p>{money(product.price_kopecks)}</p>
      <button onClick={onClose}>Закрыть карточку</button>
    </section>
  );
}
