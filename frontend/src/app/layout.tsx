import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CrossBorder AI Copilot",
  description: "Cross-border e-commerce product comparison & Amazon listing generator",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-gray-50">
            <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-4">
              <span className="font-semibold text-gray-900 text-lg">CrossBorder AI Copilot</span>
              <a href="/" className="text-sm text-gray-500 hover:text-gray-900">Analyze</a>
              <a href="/batch" className="text-sm text-gray-500 hover:text-gray-900">Batch</a>
              <div className="flex-1" />
              <a href="/settings" className="text-sm text-gray-500 hover:text-gray-900">⚙ Settings</a>
            </nav>
            <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
          </div>
        </Providers>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
