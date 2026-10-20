import type { Metadata } from "next";
import Script from "next/script";
import "./style.css";

export const metadata: Metadata = {
  title: "Каталог",
  description: "Каталог товаров",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
        <main>{children}</main>
      </body>
    </html>
  );
}
