/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#6B8DAF',
        secondary: '#0D2C4B',
        accent: '#1A2C47',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}