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
    <html lang="ru" className={manrope.variable} suppressHydrationWarning>
      <body className="min-h-screen font-sans antialiased">
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
