/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          primary: '#16324F',
          secondary: '#2F5D8A',
          hover: '#1D4066',
          active: '#10243A',
        },
        accent: {
          blue: '#4A90E2',
        },
        bg: {
          primary: '#F8FBFF',
          secondary: '#EEF5FC',
        },
        text: {
          primary: '#10243A',
          secondary: '#5B7083',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
