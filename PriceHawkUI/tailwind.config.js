/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // PriceHawk Design System Colors
        primary: {
          DEFAULT: '#0EA5E9', // sky-500 - main brand color
          hover: '#0284C7',   // sky-600 - hover state
          light: '#38BDF8',   // sky-400 - lighter variant
        },
        status: {
          cheapest: '#22C55E',  // green-500
          higher: '#EF4444',    // red-500
          same: '#6B7280',      // gray-500
          unavailable: '#D1D5DB', // gray-300
        },
      },
    },
  },
  plugins: [],
}
