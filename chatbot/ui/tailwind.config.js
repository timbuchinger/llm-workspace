/** @type {import('tailwindcss').Config} */
export default {
  purge: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  content: [],
  theme: {
    extend: {
    colors: {
        transparent: 'transparent',
        current: 'currentColor',
        'default': {
          '50': '#f1f7ee',
            '100': '#e0eed9',
            '200': '#c5deb8',
            '300': '#a1c88e',
            '400': '#7fb269',
            '500': '#61974b',
            '600': '#4a7739',
            '700': '#38582d',
            '800': '#324a2a',
            '900': '#2d4027',
            '950': '#152211',
        },
        'secondary': {
          '50': '#fef6ee',
        '100': '#fdebd7',
        '200': '#fbd3ad',
        '300': '#f7b47a',
        '400': '#f49352',
        '500': '#f06b1f',
        '600': '#e15115',
        '700': '#ba3c14',
        '800': '#943118',
        '900': '#782a16',
        '950': '#411209',
        },
      },
    },
},
  plugins: [],
}

