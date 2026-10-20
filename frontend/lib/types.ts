export type Product = { id: number; name: string; price_kopecks: number };
export type CartItem = Product & { quantity: number };
export type OrderInput = { request_id: string; name: string; contact: string };
export type Order = { id: string; total_kopecks: number };
