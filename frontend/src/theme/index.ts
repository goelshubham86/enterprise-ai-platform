import { createTheme, alpha } from '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Palette {
    sidebar: {
      bg: string;
      text: string;
      active: string;
      hover: string;
      border: string;
    };
  }
  interface PaletteOptions {
    sidebar?: {
      bg: string;
      text: string;
      active: string;
      hover: string;
      border: string;
    };
  }
}

const GOOGLE_BLUE = '#1a73e8';
const SIDEBAR_BG = '#202124';
const SIDEBAR_HOVER = '#3c4043';
const SIDEBAR_ACTIVE = alpha(GOOGLE_BLUE, 0.15);

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: GOOGLE_BLUE,
      light: '#4285f4',
      dark: '#1557b0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#00897b',
      light: '#26a69a',
      dark: '#00695c',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d93025',
    },
    warning: {
      main: '#f9ab00',
    },
    success: {
      main: '#34a853',
    },
    background: {
      default: '#f1f3f4',
      paper: '#ffffff',
    },
    text: {
      primary: '#202124',
      secondary: '#5f6368',
    },
    divider: '#dadce0',
    sidebar: {
      bg: SIDEBAR_BG,
      text: '#bdc1c6',
      active: SIDEBAR_ACTIVE,
      hover: SIDEBAR_HOVER,
      border: '#3c4043',
    },
  },
  typography: {
    fontFamily: [
      '"Google Sans"',
      'Roboto',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'sans-serif',
    ].join(','),
    h1: { fontWeight: 400, fontSize: '2rem' },
    h2: { fontWeight: 400, fontSize: '1.5rem' },
    h3: { fontWeight: 500, fontSize: '1.25rem' },
    h4: { fontWeight: 500, fontSize: '1.125rem' },
    h5: { fontWeight: 500, fontSize: '1rem' },
    h6: { fontWeight: 500, fontSize: '0.875rem' },
    body1: { fontSize: '0.875rem' },
    body2: { fontSize: '0.8125rem' },
    caption: { fontSize: '0.75rem', color: '#5f6368' },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: 6,
          boxShadow: 'none',
          '&:hover': { boxShadow: 'none' },
        },
        containedPrimary: {
          '&:hover': { backgroundColor: '#1557b0' },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          border: '1px solid #dadce0',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 1px 3px rgba(60,64,67,.15), 0 4px 8px rgba(60,64,67,.1)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', size: 'small' },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: GOOGLE_BLUE,
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#3c4043',
          fontSize: '0.75rem',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#202124',
          boxShadow: '0 1px 0 #dadce0',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
  },
});
