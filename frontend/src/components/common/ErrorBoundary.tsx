import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import { BugReportOutlined, RefreshOutlined } from '@mui/icons-material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            p: 4,
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 5,
              maxWidth: 480,
              textAlign: 'center',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 3,
            }}
          >
            <BugReportOutlined sx={{ fontSize: 56, color: 'error.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom fontWeight={500}>
              Application Error
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {this.state.error?.message ?? 'An unexpected error occurred in the application.'}
            </Typography>
            <Button
              variant="contained"
              startIcon={<RefreshOutlined />}
              onClick={this.handleReset}
            >
              Try again
            </Button>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}
