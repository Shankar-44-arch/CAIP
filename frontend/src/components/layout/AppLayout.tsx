import { type ReactNode, useState } from 'react';
import {
  Box, Drawer, AppBar, Toolbar, Typography, List, ListItemButton,
  ListItemIcon, ListItemText, IconButton, Chip, Divider, Button,
} from '@mui/material';
import {
  Dashboard, Place, Timeline, Hub, PersonSearch, Insights,
  NotificationsActive, Menu as MenuIcon, Shield, Logout, CloudUpload, Person
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { caipPalette } from '@/theme/theme';

const DRAWER_WIDTH = 248;

const NAV_ITEMS = [
  { label: 'Executive Dashboard', icon: <Dashboard />, path: '/' },
  { label: 'District Ranking', icon: <Place />, path: '/district-ranking' },
  { label: 'Crime Trend', icon: <Timeline />, path: '/trend' },
  { label: 'Criminal Network', icon: <Hub />, path: '/network' },
  { label: 'Repeat Offenders', icon: <PersonSearch />, path: '/offenders' },
  { label: 'Anomaly Detection', icon: <NotificationsActive />, path: '/anomalies' },
  { label: 'Upload Data', icon: <CloudUpload />, path: '/upload' },
  { label: 'My Profile', icon: <Person />, path: '/profile' },
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('caip_access_token');
    window.dispatchEvent(new Event('auth_change'));
    navigate('/login');
  };

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar sx={{ gap: 1.5, px: 2.5 }}>
        <Shield sx={{ color: caipPalette.signalCyan }} />
        <Box>
          <Typography variant="subtitle1" fontWeight={700} lineHeight={1.1}>CAIP</Typography>
          <Typography variant="overline" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
            Karnataka Intelligence
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List sx={{ px: 1.5, py: 2, flex: 1 }}>
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.path}
              selected={active}
              onClick={() => { navigate(item.path); setMobileOpen(false); }}
              sx={{
                borderRadius: 1.5, mb: 0.5,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(63,214,208,0.10)',
                  borderLeft: `2px solid ${caipPalette.signalCyan}`,
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 38, color: active ? caipPalette.signalCyan : 'text.secondary' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: '0.875rem' }} />
            </ListItemButton>
          );
        })}
      </List>
      <Divider />
      <Box sx={{ p: 2 }}>
        <Button startIcon={<Logout />} onClick={handleLogout} size="small" fullWidth variant="outlined">
          Sign Out
        </Button>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: 'background.paper',
          borderBottom: `1px solid ${caipPalette.hairline}`,
        }}
      >
        <Toolbar sx={{ gap: 2 }}>
          <IconButton sx={{ display: { md: 'none' } }} onClick={() => setMobileOpen(true)}>
            <MenuIcon />
          </IconButton>
          <Typography variant="overline" color="text.secondary">KARNATAKA CRIME INTELLIGENCE</Typography>
          <Box sx={{ flex: 1 }} />
          <Chip size="small" label="HISTORICAL DATA" sx={{ bgcolor: 'rgba(63,182,138,0.12)', color: caipPalette.riskLow }} />
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{ display: { xs: 'none', md: 'block' }, '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box component="main" sx={{ flexGrow: 1, width: { md: `calc(100% - ${DRAWER_WIDTH}px)` }, minHeight: '100vh' }}>
        <Toolbar />
        <Box sx={{ p: { xs: 2, md: 3 } }}>{children}</Box>
      </Box>
    </Box>
  );
}
