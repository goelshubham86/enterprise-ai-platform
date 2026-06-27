import { Box, Typography, Button } from '@mui/material';
import { HomeOutlined } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '@/utils/constants';

export function NotFound() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        px: 4,
      }}
    >
      <Typography
        variant="h1"
        sx={{ fontSize: '6rem', fontWeight: 300, color: 'text.disabled', lineHeight: 1 }}
      >
        404
      </Typography>
      <Typography variant="h4" fontWeight={400} gutterBottom sx={{ mt: 2 }}>
        Page not found
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 400 }}>
        The page you're looking for doesn't exist or has been moved.
      </Typography>
      <Button
        variant="contained"
        startIcon={<HomeOutlined />}
        onClick={() => navigate(ROUTES.dashboard)}
      >
        Back to Dashboard
      </Button>
    </Box>
  );
}
