import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PriceHawk - Price Monitoring System',
  description: 'Compare prices across Thai home improvement retailers',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
