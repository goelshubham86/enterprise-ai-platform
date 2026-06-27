import { Alert, AlertTitle, Button, Box } from '@mui/material';
import { RefreshOutlined } from '@mui/icons-material';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorMessageProps) {
  return (
    <Box sx={{ py: 4, px: 2 }}>
      <Alert
        severity="error"
        action={
          onRetry ? (
            <Button
              size="small"
              startIcon={<RefreshOutlined />}
              onClick={onRetry}
              color="inherit"
            >
              Retry
            </Button>
          ) : undefined
        }
        sx={{ borderRadius: 2 }}
      >
        <AlertTitle>{title}</AlertTitle>
        {message}
      </Alert>
    </Box>
  );
}
