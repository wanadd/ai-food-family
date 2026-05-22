import type { Metadata } from "next";
import Script from "next/script";

import { AppProviders } from "@/components/AppProviders";
import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "ПланАм",
  description: "ПланАм помогает составить меню и список покупок для себя и семьи",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-white text-stone-900 antialiased">
        <Script
          src="https://telegram.org/js/telegram-web-app.js"
          strategy="afterInteractive"
        />
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
