const STORAGE_KEY = "checkout_request";

export function checkoutKey(): string {
  const existing = sessionStorage.getItem(STORAGE_KEY);
  return existing || newCheckoutKey();
}

export function newCheckoutKey(): string {
  const key = crypto.randomUUID();
  sessionStorage.setItem(STORAGE_KEY, key);
  return key;
}
