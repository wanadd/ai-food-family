import type { Metadata } from "next";
import { Manrope } from "next/font/google";

import { AppProviders } from "@/components/AppProviders";
import "./globals.css";

export const dynamic = "force-dynamic";

const manrope = Manrope({
  subsets: ["latin", "cyrillic"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-manrope",
  display: "swap",
});

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
    <html lang="ru" className={manrope.variable}>
      <body className="min-h-screen bg-cream font-sans text-graphite-900 antialiased">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
