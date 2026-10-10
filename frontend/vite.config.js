import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'DueTime',
        short_name: 'DueTime',
        description: "Know what your car needs before it breaks.",
        theme_color: '#14532d',
        background_color: '#f7f6f2',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        // Reports the judges already opened keep working if venue Wi-Fi drops.
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/report'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'duetime-reports',
              networkTimeoutSeconds: 6,
              expiration: { maxEntries: 20 }
            }
          }
        ]
      }
    })
  ]
})
