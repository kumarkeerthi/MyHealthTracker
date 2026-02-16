import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Metabolic OS',
    short_name: 'MetOS',
    description: 'Premium metabolic dashboard',
    start_url: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#0f172a',
    theme_color: '#0f172a',
    icons: [
      { src: '/icons/icon-192.svg', sizes: '192x192', type: 'image/svg+xml' },
      { src: '/icons/icon-512.svg', sizes: '512x512', type: 'image/svg+xml' },
      { src: '/icons/icon-maskable.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'maskable' },
    ],
  };
}
