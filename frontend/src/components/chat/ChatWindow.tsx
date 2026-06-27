import { useEffect, useRef } from 'react';
import { Box, Typography, Divider } from '@mui/material';
import { AutoAwesomeOutlined } from '@mui/icons-material';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import type { ChatMessage } from '@/types';

const WELCOME_HINTS = [
  'Summarize the key findings from our Q4 risk assessment',
  'What are the compliance requirements for customer data handling?',
  'List the architecture decisions from our cloud migration plan',
  'Find all mentions of data retention policies',
];

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSend: (question: string) => void;
  sessionId: string | null;
}

function WelcomeScreen({ onSend }: { onSend: (q: string) => void }) {
  return (
    <Box
      sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        px: 4,
        py: 8,
        textAlign: 'center',
      }}
    >
      <Box
        sx={{
          width: 64,
          height: 64,
          borderRadius: '50%',
          bgcolor: 'primary.main',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 3,
        }}
      >
        <AutoAwesomeOutlined sx={{ fontSize: 32, color: '#fff' }} />
      </Box>

      <Typography variant="h4" fontWeight={400} gutterBottom>
        Enterprise AI Knowledge Assistant
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 480, mb: 4 }}>
        Ask questions across your indexed enterprise documents. Responses are grounded in your
        document library using Retrieval-Augmented Generation.
      </Typography>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
          gap: 1.5,
          maxWidth: 600,
          width: '100%',
        }}
      >
        {WELCOME_HINTS.map((hint) => (
          <Box
            key={hint}
            onClick={() => onSend(hint)}
            sx={{
              p: 2,
              borderRadius: 2,
              border: '1px solid',
              borderColor: 'divider',
              bgcolor: 'background.paper',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s ease',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'rgba(26,115,232,0.04)',
              },
            }}
          >
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8125rem' }}>
              "{hint}"
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

function TypingIndicator() {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.5 }}>
      <Box
        sx={{
          width: 34,
          height: 34,
          borderRadius: '50%',
          bgcolor: '#f1f3f4',
          border: '1px solid #dadce0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <AutoAwesomeOutlined sx={{ fontSize: 18, color: 'primary.main' }} />
      </Box>
      <Box
        sx={{
          bgcolor: '#fff',
          border: '1px solid #dadce0',
          borderRadius: '4px 18px 18px 18px',
          px: 2,
          py: 1.5,
        }}
      >
        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
          {[0, 1, 2].map((i) => (
            <Box
              key={i}
              sx={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                bgcolor: 'text.disabled',
                animation: 'pulse 1.4s ease-in-out infinite',
                animationDelay: `${i * 0.2}s`,
                '@keyframes pulse': {
                  '0%, 80%, 100%': { opacity: 0.3 },
                  '40%': { opacity: 1 },
                },
              }}
            />
          ))}
        </Box>
      </Box>
    </Box>
  );
}

export function ChatWindow({ messages, isLoading, onSend, sessionId }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Message list */}
      <Box sx={{ flex: 1, overflowY: 'auto', px: { xs: 0, sm: 2 } }}>
        {messages.length === 0 ? (
          <WelcomeScreen onSend={onSend} />
        ) : (
          <Box sx={{ maxWidth: 800, mx: 'auto', py: 3 }}>
            {messages.map((msg, i) => (
              <Box key={msg.id}>
                <MessageBubble message={msg} />
                {i < messages.length - 1 && (
                  <Divider sx={{ my: 0.5, borderColor: 'transparent' }} />
                )}
              </Box>
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} />
          </Box>
        )}
      </Box>

      {/* Session indicator */}
      {sessionId && (
        <Box sx={{ px: 2, py: 0.5, textAlign: 'center' }}>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.7rem' }}>
            Session · {sessionId.slice(0, 8)}
          </Typography>
        </Box>
      )}

      {/* Input */}
      <Box
        sx={{
          px: { xs: 0, sm: 2 },
          pb: 2,
          pt: 1,
          maxWidth: 800,
          mx: 'auto',
          width: '100%',
        }}
      >
        <ChatInput onSend={onSend} isLoading={isLoading} />
      </Box>
    </Box>
  );
}
