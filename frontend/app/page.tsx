"use client";

import { useEffect, useState } from "react";
import { Cart } from "../components/Cart";
import { ProductDetails } from "../components/ProductDetails";
import { ProductList } from "../components/ProductList";
import * as api from "../lib/api";
import { checkoutKey, newCheckoutKey } from "../lib/checkout";
import { money } from "../lib/money";
import type { CartItem, Product } from "../lib/types";

const PAGE_SIZE = 20;

export default function Catalog() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selected, setSelected] = useState<Product | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [requestId, setRequestId] = useState("");

  useEffect(() => {
    const telegram = (
      window as Window & {
        Telegram?: { WebApp?: { ready(): void; expand(): void } };
      }
    ).Telegram?.WebApp;
    telegram?.ready();
    telegram?.expand();
    setRequestId(checkoutKey());
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      api.getProducts(PAGE_SIZE + 1, page * PAGE_SIZE),
      api.getCart(),
    ])
      .then(([catalog, basket]) => {
        if (!active) return;
        setProducts(catalog.items.slice(0, PAGE_SIZE));
        setHasNext(catalog.items.length > PAGE_SIZE);
        setCart(basket.items);
        setError("");
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page]);

  async function change(product: Product, quantity: number) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      setCart((await api.setQuantity(product.id, quantity)).items);
      setRequestId(newCheckoutKey());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function checkout(name: string, contact: string): Promise<boolean> {
    setBusy(true);
    setError("");
    try {
      const order = await api.createOrder({
        request_id: requestId,
        name,
        contact,
      });
      setCart((await api.getCart()).items);
      setNotice(
        `Заказ оформлен на сумму ${money(order.total_kopecks)}. Оплата не требуется.`,
      );
      setRequestId(newCheckoutKey());
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1>Каталог</h1>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {loading ? (
        <p>Загрузка…</p>
      ) : (
        <>
          <ProductList
            products={products}
            cart={cart}
            busy={busy}
            onSelect={setSelected}
            onChange={change}
          />
          <nav aria-label="Страницы каталога">
            <button disabled={!page || busy} onClick={() => setPage(page - 1)}>
              Назад
            </button>
            <span>Страница {page + 1}</span>
            <button
              disabled={!hasNext || busy}
              onClick={() => setPage(page + 1)}
            >
              Далее
            </button>
          </nav>
        </>
      )}
      {selected && (
        <ProductDetails product={selected} onClose={() => setSelected(null)} />
      )}
      <Cart
        items={cart}
        busy={busy || loading}
        ready={Boolean(requestId)}
        onChange={change}
        onCheckout={checkout}
      />
    </>
  );
}
