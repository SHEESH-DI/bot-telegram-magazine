import type { FormEvent } from "react";
import { money } from "../lib/money";
import type { CartItem, Product } from "../lib/types";

type Props = {
  items: CartItem[];
  busy: boolean;
  ready: boolean;
  onChange(product: Product, quantity: number): Promise<void>;
  onCheckout(name: string, contact: string): Promise<boolean>;
};

export function Cart({ items, busy, ready, onChange, onCheckout }: Props) {
  const total = items.reduce(
    (sum, item) => sum + item.price_kopecks * item.quantity,
    0,
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    if (
      await onCheckout(
        String(fields.get("name") ?? ""),
        String(fields.get("contact") ?? ""),
      )
    )
      form.reset();
  }

  return (
    <section>
      <h2>Корзина</h2>
      {!items.length ? (
        <p>Корзина пуста</p>
      ) : (
        <>
          <ul>
            {items.map((item) => (
              <li key={item.id}>
                {item.name} — {item.quantity} шт. × {money(item.price_kopecks)}{" "}
                = {money(item.price_kopecks * item.quantity)}
                <button
                  aria-label={`Уменьшить ${item.name}`}
                  disabled={busy}
                  onClick={() => onChange(item, item.quantity - 1)}
                >
                  −
                </button>
                <button
                  aria-label={`Увеличить ${item.name}`}
                  disabled={busy || item.quantity >= 99}
                  onClick={() => onChange(item, item.quantity + 1)}
                >
                  +
                </button>
                <button disabled={busy} onClick={() => onChange(item, 0)}>
                  Удалить
                </button>
              </li>
            ))}
          </ul>
          <p>
            <strong>Итого: {money(total)}</strong>
          </p>
          <h3>Оформить заказ</h3>
          <p>Тестовые цены. Оплата не требуется.</p>
          <form onSubmit={submit}>
            <label>
              Имя
              <input name="name" required maxLength={200} />
            </label>
            <label>
              Контакт для связи
              <input name="contact" required maxLength={300} />
            </label>
            <button disabled={busy || !ready}>Оформить заказ</button>
          </form>
        </>
      )}
    </section>
  );
}
