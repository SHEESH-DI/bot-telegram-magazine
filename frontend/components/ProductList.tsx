import type { CartItem, Product } from "../lib/types";
import { money } from "../lib/money";

type Props = {
  products: Product[];
  cart: CartItem[];
  busy: boolean;
  onSelect(product: Product): void;
  onChange(product: Product, quantity: number): Promise<void>;
};

export function ProductList({
  products,
  cart,
  busy,
  onSelect,
  onChange,
}: Props) {
  if (!products.length)
    return <p>Товаров пока нет. Администратор может добавить их через бота.</p>;
  return (
    <ul className="products">
      {products.map((product) => {
        const quantity =
          cart.find((item) => item.id === product.id)?.quantity ?? 0;
        return (
          <li key={product.id}>
            <img
              src={`/api/products/${product.id}/image`}
              alt={product.name}
              width={180}
              height={135}
            />
            <h2>
              <button onClick={() => onSelect(product)}>{product.name}</button>
            </h2>
            <p>{money(product.price_kopecks)}</p>
            <button
              disabled={busy || quantity >= 99}
              onClick={() => onChange(product, quantity + 1)}
            >
              В корзину
            </button>
          </li>
        );
      })}
    </ul>
  );
}
