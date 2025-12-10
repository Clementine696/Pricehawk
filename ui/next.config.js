/** @type {import('next').NextConfig} */
const nextConfig = {
  // Only proxy API calls in local development
  // In production (Vercel), api.ts uses NEXT_PUBLIC_API_URL directly
  async rewrites() {
    // Vercel automatically sets VERCEL=1 during builds
    // Skip rewrites in production - let api.ts handle the full URL
    if (process.env.VERCEL) {
      console.log('[next.config.js] Running on Vercel - skipping API rewrites');
      return [];
    }
    // Local development: proxy to local backend
    console.log('[next.config.js] Local dev - proxying /api/* to localhost:8000');
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
