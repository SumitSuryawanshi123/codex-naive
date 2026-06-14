/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif']
      },
      boxShadow: {
        soft: '0 18px 50px rgba(31, 41, 55, 0.12)'
      }
    }
  },
  plugins: []
};

