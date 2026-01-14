import type { Metadata } from 'next';
import Script from 'next/script';
import { AuthProvider } from '@/context/AuthContext';
import PageViewTracker from '@/components/PageViewTracker';
import './globals.css';

export const metadata: Metadata = {
  title: 'PriceHawk',
  description: 'Price tracking application',
};

const GA_TRACKING_ID = 'G-Y4YCTMYX01';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_TRACKING_ID}', {
              page_path: window.location.pathname,
              send_page_view: true,
              // Enable enhanced measurement features
              anonymize_ip: false,
              cookie_flags: 'SameSite=None;Secure',
              // Enable engagement metrics
              engagement_time_msec: 100,
            });
          `}
        </Script>
      </head>
      <body>
        <AuthProvider>
          <PageViewTracker />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
