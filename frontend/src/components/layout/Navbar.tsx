import {
  AppBar,
  Toolbar,
  IconButton,
  Box,
  Typography,
  Tooltip,
  Avatar,
  Chip,
  useMediaQuery,
} from '@mui/material';
import {
  MenuOutlined,
  NotificationsOutlined,
  HelpOutlineOutlined,
  SearchOutlined,
} from '@mui/icons-material';
import { useLocation } from 'react-router-dom';
import { theme } from '@/theme';
import { SIDEBAR_WIDTH, NAVBAR_HEIGHT } from '@/utils/constants';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/chat': 'AI Chat',
  '/documents': 'Documents',
  '/settings': 'Settings',
  '/health': 'System Health',
};

interface NavbarProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

export function Navbar({ onMenuClick, sidebarOpen }: NavbarProps) {
  const location = useLocation();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const pageTitle = PAGE_TITLES[location.pathname] ?? 'Enterprise AI Assistant';

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        height: NAVBAR_HEIGHT,
        ml: isDesktop && sidebarOpen ? `${SIDEBAR_WIDTH}px` : 0,
        width: isDesktop && sidebarOpen ? `calc(100% - ${SIDEBAR_WIDTH}px)` : '100%',
        transition: theme.transitions.create(['width', 'margin'], {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.leavingScreen,
        }),
      }}
    >
      <Toolbar sx={{ height: NAVBAR_HEIGHT, gap: 1 }}>
        {!isDesktop && (
          <IconButton
            onClick={onMenuClick}
            edge="start"
            aria-label="open sidebar"
            size="medium"
          >
            <MenuOutlined />
          </IconButton>
        )}

        <Typography
          variant="h6"
          sx={{
            fontWeight: 500,
            color: 'text.primary',
            fontSize: '1.0625rem',
          }}
        >
          {pageTitle}
        </Typography>

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Search (coming soon)">
          <IconButton size="medium" aria-label="global search">
            <SearchOutlined sx={{ color: 'text.secondary' }} />
          </IconButton>
        </Tooltip>

        <Tooltip title="Notifications">
          <IconButton size="medium" aria-label="notifications">
            <NotificationsOutlined sx={{ color: 'text.secondary' }} />
          </IconButton>
        </Tooltip>

        <Tooltip title="Help & documentation">
          <IconButton size="medium" aria-label="help">
            <HelpOutlineOutlined sx={{ color: 'text.secondary' }} />
          </IconButton>
        </Tooltip>

        <Chip
          avatar={
            <Avatar
              sx={{ bgcolor: theme.palette.primary.main, width: 28, height: 28, fontSize: '0.75rem' }}
            >
              EA
            </Avatar>
          }
          label="Enterprise"
          variant="outlined"
          size="small"
          sx={{ borderRadius: 6, borderColor: 'divider', cursor: 'pointer' }}
        />
      </Toolbar>
    </AppBar>
  );
}
