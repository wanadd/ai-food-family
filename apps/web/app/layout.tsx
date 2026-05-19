import type { Metadata } from "next";
import Script from "next/script";

import { TelegramProvider } from "@/components/TelegramProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Food Family",
  description: "Telegram Mini App for AI Food Family",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <head>
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="beforeInteractive"
        />
      </head>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <TelegramProvider>{children}</TelegramProvider>
      </body>
    </html>
  );
}
