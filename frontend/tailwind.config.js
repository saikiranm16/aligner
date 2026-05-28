/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#06121f",
          900: "#0d1b2a",
          800: "#13263a",
        },
        sand: "#f7f4ea",
        accent: "#0f766e",
        glow: "#f59e0b",
      },
      boxShadow: {
        panel: "0 18px 40px rgba(15, 23, 42, 0.18)",
        darkpanel: "0 18px 44px rgba(2, 6, 23, 0.55)",
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at 20% 20%, rgba(245,158,11,0.18), transparent 28%), radial-gradient(circle at 80% 0%, rgba(15,118,110,0.18), transparent 24%), linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%)",
      },
    },
  },
  plugins: [],
};

