import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Metabolic Intelligence Engine',
    short_name: 'MIE',
    description: 'Premium metabolic dashboard',
    start_url: '/',
    display: 'standalone',
    background_color: '#05070C',
    theme_color: '#05070C',
    icons: [
      {
        src: '/icon.svg',
        sizes: 'any',
        type: 'image/svg+xml',
      },
    ],
  };
}
