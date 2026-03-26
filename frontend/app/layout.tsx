import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Insurance Document RAG MVP",
  description: "Simple frontend skeleton for upload, chat, and evaluation.",
};

const navItems = [
  { href: "/upload", label: "Upload" },
  { href: "/chat", label: "Chat" },
  { href: "/evaluation", label: "Evaluation" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="header">
            <div>
              <p className="eyebrow">Insurance Document RAG MVP</p>
              <h1>Uploaded Insurance documents</h1>
            </div>
            <nav className="nav">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
