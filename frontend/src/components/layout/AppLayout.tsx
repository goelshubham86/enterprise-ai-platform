import { useState } from 'react';
import { Box, useMediaQuery } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { theme } from '@/theme';
import { SIDEBAR_WIDTH, NAVBAR_HEIGHT } from '@/utils/constants';

export function AppLayout() {
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleMenuClick = () => setMobileOpen((prev) => !prev);
  const handleDrawerClose = () => setMobileOpen(false);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Permanent sidebar on desktop */}
      {isDesktop ? (
        <Sidebar open variant="permanent" onClose={handleDrawerClose} />
      ) : (
        <Sidebar open={mobileOpen} variant="temporary" onClose={handleDrawerClose} />
      )}

      {/* Main content area */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          flex: 1,
          minWidth: 0,
          ml: isDesktop ? `${SIDEBAR_WIDTH}px` : 0,
        }}
      >
        <Navbar onMenuClick={handleMenuClick} sidebarOpen={isDesktop} />

        <Box
          component="main"
          sx={{
            flex: 1,
            mt: `${NAVBAR_HEIGHT}px`,
            p: { xs: 2, sm: 3 },
            overflowY: 'auto',
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
