/** @type {import('next').NextConfig} */
const nextConfig = {
  // Only proxy API calls in development (when no NEXT_PUBLIC_API_URL is set)
  // In production, api.ts uses NEXT_PUBLIC_API_URL directly
  async rewrites() {
    // Skip rewrites in production - let api.ts handle the full URL
    if (process.env.NEXT_PUBLIC_API_URL) {
      return [];
    }
    // Local development: proxy to local backend
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
