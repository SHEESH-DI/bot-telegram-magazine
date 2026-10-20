const currency = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
});

export function money(kopecks: number): string {
  return currency.format(kopecks / 100);
}
