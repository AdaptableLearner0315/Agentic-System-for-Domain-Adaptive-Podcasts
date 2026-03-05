/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Warm Suno AI-inspired dark theme
        background: 'hsl(20 15% 6%)',
        foreground: 'hsl(30 20% 92%)',
        card: {
          DEFAULT: 'hsl(20 12% 10%)',
          foreground: 'hsl(30 20% 92%)',
        },
        popover: {
          DEFAULT: 'hsl(20 12% 10%)',
          foreground: 'hsl(30 20% 92%)',
        },
        primary: {
          DEFAULT: 'hsl(24 90% 55%)',
          foreground: 'hsl(20 15% 6%)',
        },
        secondary: {
          DEFAULT: 'hsl(20 10% 15%)',
          foreground: 'hsl(30 20% 92%)',
        },
        muted: {
          DEFAULT: 'hsl(20 10% 13%)',
          foreground: 'hsl(25 10% 55%)',
        },
        accent: {
          DEFAULT: 'hsl(12 80% 55%)',
          foreground: 'hsl(30 20% 92%)',
        },
        destructive: {
          DEFAULT: 'hsl(0 84% 60%)',
          foreground: 'hsl(30 20% 92%)',
        },
        success: {
          DEFAULT: 'hsl(142 76% 36%)',
          foreground: 'hsl(30 20% 92%)',
        },
        warning: {
          DEFAULT: 'hsl(38 92% 50%)',
          foreground: 'hsl(20 15% 6%)',
        },
        border: 'hsl(20 10% 18%)',
        input: 'hsl(20 10% 13%)',
        ring: 'hsl(24 90% 55%)',
      },
      borderRadius: {
        lg: '0.75rem',
        md: '0.5rem',
        sm: '0.25rem',
      },
      fontFamily: {
        sans: ['DM Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.5 },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
        'slide-out-up': {
          '0%': { transform: 'translateY(0)', opacity: 1 },
          '100%': { transform: 'translateY(-20px)', opacity: 0 },
        },
        'slide-in-up': {
          '0%': { transform: 'translateY(20px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
      },
      animation: {
        'pulse-slow': 'pulse-slow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'slide-out-up': 'slide-out-up 0.3s ease-out forwards',
        'slide-in-up': 'slide-in-up 0.3s ease-out',
      },
    },
  },
  plugins: [],
}
