import type { CartItem, Order, OrderInput, Product } from "./types";

async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/${path}`, {
      method,
      credentials: "same-origin",
      cache: "no-store",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Не удалось связаться с сервером. Попробуйте ещё раз.");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : "Не удалось выполнить запрос. Попробуйте ещё раз.",
    );
  }
  if (data === null) throw new Error("Сервер вернул некорректный ответ");
  return data as T;
}

export const getProducts = (limit: number, offset: number) =>
  request<{ items: Product[] }>(`products?limit=${limit}&offset=${offset}`);
export const getCart = () => request<{ items: CartItem[] }>("cart");
export const setQuantity = (productId: number, quantity: number) =>
  request<{ items: CartItem[] }>(`cart/${productId}`, "PUT", { quantity });
export const createOrder = (body: OrderInput) =>
  request<Order>("orders", "POST", body);
