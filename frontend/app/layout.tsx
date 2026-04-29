import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/src/lib/session-context";

const geist = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "The Abstract Enclave — AI-Powered Psychometric Assessment",
  description:
    "An interactive, AI-powered behavioral assessment measuring Confidence, Curiosity, Emotional Safety, and Exploratory Power through immersive narrative puzzles.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-[#0a0a1a]">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
