import type { Metadata } from "next";
import { Cormorant_Garamond, Inter } from "next/font/google";
import { AppStoreProvider } from "@/app/context/AppStoreContext";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
});

const cormorantGaramond = Cormorant_Garamond({
  variable: "--font-cormorant",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "AI Clothes Recommendation",
  description:
    "AI-powered outfit recommendations curated for your occasion, style, and preferences.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${cormorantGaramond.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AppStoreProvider>{children}</AppStoreProvider>
      </body>
    </html>
  );
}
