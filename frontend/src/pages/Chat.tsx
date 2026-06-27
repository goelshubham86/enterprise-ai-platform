import { Box, Button, Typography, Tooltip, IconButton } from '@mui/material';
import { DeleteOutlined, AddOutlined } from '@mui/icons-material';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { useChat } from '@/hooks/useChat';

export function Chat() {
  const { messages, sessionId, isLoading, error, send, clearSession } = useChat();

  return (
    <Box
      sx={{
        height: 'calc(100vh - 64px - 48px)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Session toolbar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          px: 0.5,
        }}
      >
        <Box>
          <Typography variant="h5" fontWeight={500}>
            AI Knowledge Chat
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Grounded in your indexed document library · Vertex AI Gemini
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="New session">
            <span>
              <IconButton
                size="small"
                onClick={clearSession}
                disabled={messages.length === 0}
              >
                <AddOutlined />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title="Clear conversation">
            <span>
              <Button
                size="small"
                startIcon={<DeleteOutlined />}
                onClick={clearSession}
                disabled={messages.length === 0}
                variant="outlined"
                color="inherit"
                sx={{ borderColor: 'divider' }}
              >
                Clear
              </Button>
            </span>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <ErrorMessage
          title="Failed to get a response"
          message={(error as Error).message}
          onRetry={undefined}
        />
      )}

      <Box sx={{ flex: 1, minHeight: 0 }}>
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={send}
          sessionId={sessionId}
        />
      </Box>
    </Box>
  );
}
