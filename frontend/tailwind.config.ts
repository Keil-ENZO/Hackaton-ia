import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: "#0B0E14",       // fond quasi noir
        panel: "#11151D",      // panneaux
        border: "#1E2430",     // bordures subtiles
        foreground: "#E8EAED", // texte principal
        muted: "#8891A0",      // texte secondaire gris-bleu
        accent: "#5EEAD4",     // teal (interactif/actif)
        source: "#F5A623",     // amber (citations de sources)
      },
      fontFamily: {
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
