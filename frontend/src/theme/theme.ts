/**
 * CAIP-Karnataka Design System — "Night Watch"
 * Dark command-center theme. Domain-agnostic (no US/demo content).
 */
import { createTheme } from '@mui/material/styles';

export const caipPalette = {
  bgDeep: '#0B0F14',
  bgPanel: '#121821',
  hairline: '#243040',
  textPrimary: '#E8EDF3',
  textSecondary: '#8B98A9',
  signalCyan: '#3FD6D0',
  signalAmber: '#F5A623',
  riskLow: '#3FB68A',
  riskMedium: '#F5C744',
  riskHigh: '#F5853F',
  riskCritical: '#E0473E',
};

export const theme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: caipPalette.bgDeep, paper: caipPalette.bgPanel },
    primary: { main: caipPalette.signalCyan, contrastText: '#06141A' },
    secondary: { main: caipPalette.signalAmber, contrastText: '#1A1100' },
    error: { main: caipPalette.riskCritical },
    warning: { main: caipPalette.riskHigh },
    success: { main: caipPalette.riskLow },
    text: { primary: caipPalette.textPrimary, secondary: caipPalette.textSecondary },
    divider: caipPalette.hairline,
  },
  typography: {
    fontFamily: '"Inter", -apple-system, "Segoe UI", sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    overline: { fontFamily: '"JetBrains Mono", monospace', letterSpacing: '0.06em' },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none', border: `1px solid ${caipPalette.hairline}` } } },
    MuiButton: { styleOverrides: { root: { textTransform: 'none', fontWeight: 600 } } },
  },
});
