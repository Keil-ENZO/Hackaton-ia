import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import "./globals.css";

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex-mono",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "DevOnboard Copilot",
  description:
    "Copilote IA d'onboarding développeur : indexez un repo et posez vos questions, réponses sourcées.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${plexMono.variable} ${inter.variable}`}>
      <body className="bg-base text-foreground font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
