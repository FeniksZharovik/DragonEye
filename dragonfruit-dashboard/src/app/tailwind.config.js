// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dragon-red': {
          100: '#FFD6DA',
          300: '#FF99AA',
          500: '#E64A6A',
          700: '#B72A45', // ← Main accent color
          900: '#8C1F38',
        },
        'dragon-pink': {
          100: '#FFE6E6',
          300: '#FFCCE0',
          500: '#FF99BB',
          700: '#D46C8A',
        },
        'dragon-purple': {
          100: '#EDE6F0',
          300: '#C8B3D5',
          500: '#8A6A99',
          700: '#6A4A70',
          800: '#4A2C42', // ← Sidebar/dark background
          900: '#3A2035',
        },
        'dragon-peach': {
          100: '#FFE6E6',
          200: '#FFD6D6',
          300: '#FFC6C6',
        },
      },
    },
  },
  plugins: [],
}