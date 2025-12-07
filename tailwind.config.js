/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'eco-green': '#22c55e',
        'eco-emerald': '#10b981',
        'eco-lime': '#84cc16',
        'eco-dark': '#166534',
        'eco-light': '#86efac',
      },
    },
  },
  plugins: [
    typography,
  ],
}
