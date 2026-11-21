/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090A0F",
        surface: "#12141D",
        surfaceHover: "#1A1D2B",
        accent: "#6366F1",
        accentNeon: "#10B981",
        viralPink: "#EC4899",
        border: "#232738"
      },
    },
  },
  plugins: [],
};
