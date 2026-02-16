import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Metabolic OS',
  description: 'Mobile-first metabolic dashboard',
  manifest: '/manifest.json',
  icons: {
    apple: '/apple-touch-icon.svg',
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'MetOS',
  },
};

export const viewport: Viewport = {
  themeColor: '#0f172a',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg text-white antialiased">{children}</body>
    </html>
  );
}
