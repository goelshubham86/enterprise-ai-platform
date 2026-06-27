import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  DashboardOutlined,
  ChatOutlined,
  FolderOutlined,
  SettingsOutlined,
  MonitorHeartOutlined,
  AutoAwesomeOutlined,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { ROUTES, SIDEBAR_WIDTH } from '@/utils/constants';
import { theme } from '@/theme';

const NAV_ITEMS = [
  { label: 'Dashboard', path: ROUTES.dashboard, icon: <DashboardOutlined /> },
  { label: 'Chat', path: ROUTES.chat, icon: <ChatOutlined /> },
  { label: 'Documents', path: ROUTES.documents, icon: <FolderOutlined /> },
  { label: 'Settings', path: ROUTES.settings, icon: <SettingsOutlined /> },
  { label: 'Health', path: ROUTES.health, icon: <MonitorHeartOutlined /> },
] as const;

const SIDEBAR_BG = theme.palette.sidebar.bg;
const SIDEBAR_TEXT = theme.palette.sidebar.text;

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  variant: 'permanent' | 'temporary';
}

function SidebarContent() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        width: SIDEBAR_WIDTH,
        height: '100%',
        bgcolor: SIDEBAR_BG,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Logo / Brand */}
      <Box
        sx={{
          px: 2.5,
          py: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          borderBottom: `1px solid ${theme.palette.sidebar.border}`,
          minHeight: 64,
        }}
      >
        <AutoAwesomeOutlined sx={{ color: '#4285f4', fontSize: 28 }} />
        <Box>
          <Typography
            variant="body2"
            sx={{ color: '#e8eaed', fontWeight: 600, lineHeight: 1.2, fontSize: '0.9rem' }}
          >
            AI Assistant
          </Typography>
          <Typography variant="caption" sx={{ color: SIDEBAR_TEXT, fontSize: '0.7rem' }}>
            Enterprise Platform
          </Typography>
        </Box>
        <Chip
          label="Beta"
          size="small"
          sx={{
            ml: 'auto',
            height: 18,
            fontSize: '0.65rem',
            bgcolor: 'rgba(66,133,244,0.2)',
            color: '#4285f4',
            border: '1px solid rgba(66,133,244,0.3)',
          }}
        />
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, py: 1, overflowY: 'auto' }}>
        <List disablePadding>
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Tooltip key={item.path} title="" placement="right">
                <ListItem disablePadding sx={{ px: 1, py: 0.25 }}>
                  <ListItemButton
                    onClick={() => navigate(item.path)}
                    selected={isActive}
                    sx={{
                      borderRadius: 1.5,
                      color: isActive ? '#ffffff' : SIDEBAR_TEXT,
                      bgcolor: isActive ? 'rgba(66,133,244,0.2)' : 'transparent',
                      '&:hover': {
                        bgcolor: isActive ? 'rgba(66,133,244,0.25)' : theme.palette.sidebar.hover,
                      },
                      '&.Mui-selected': {
                        bgcolor: 'rgba(66,133,244,0.2)',
                        '&:hover': { bgcolor: 'rgba(66,133,244,0.25)' },
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        color: isActive ? '#4285f4' : SIDEBAR_TEXT,
                        minWidth: 36,
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{
                        fontSize: '0.875rem',
                        fontWeight: isActive ? 600 : 400,
                      }}
                    />
                    {isActive && (
                      <Box
                        sx={{
                          width: 3,
                          height: 20,
                          bgcolor: '#4285f4',
                          borderRadius: 2,
                          ml: 0.5,
                        }}
                      />
                    )}
                  </ListItemButton>
                </ListItem>
              </Tooltip>
            );
          })}
        </List>
      </Box>

      {/* Footer */}
      <Divider sx={{ borderColor: theme.palette.sidebar.border }} />
      <Box sx={{ px: 2.5, py: 2 }}>
        <Typography variant="caption" sx={{ color: '#5f6368', fontSize: '0.7rem' }}>
          Powered by Vertex AI · Gemini
        </Typography>
      </Box>
    </Box>
  );
}

export function Sidebar({ open, onClose, variant }: SidebarProps) {
  return (
    <Drawer
      variant={variant}
      open={open}
      onClose={onClose}
      sx={{
        width: SIDEBAR_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: SIDEBAR_WIDTH,
          boxSizing: 'border-box',
          border: 'none',
        },
      }}
    >
      <SidebarContent />
    </Drawer>
  );
}
