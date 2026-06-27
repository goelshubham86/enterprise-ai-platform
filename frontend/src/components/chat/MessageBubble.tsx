import { Box, Typography, Paper, Collapse, IconButton, Chip, Tooltip } from '@mui/material';
import {
  PersonOutlined,
  AutoAwesomeOutlined,
  ExpandMoreOutlined,
  ExpandLessOutlined,
  ArticleOutlined,
  ContentCopyOutlined,
} from '@mui/icons-material';
import { useState } from 'react';
import type { ChatMessage } from '@/types';
import { formatDate, formatLatency } from '@/utils/formatters';
import { theme } from '@/theme';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const handleCopy = () => {
    void navigator.clipboard.writeText(message.content);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: 1.5,
        alignItems: 'flex-start',
        mb: 2.5,
      }}
    >
      {/* Avatar */}
      <Box
        sx={{
          width: 34,
          height: 34,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          bgcolor: isUser ? theme.palette.primary.main : '#f1f3f4',
          border: isUser ? 'none' : '1px solid #dadce0',
        }}
      >
        {isUser ? (
          <PersonOutlined sx={{ fontSize: 18, color: '#fff' }} />
        ) : (
          <AutoAwesomeOutlined sx={{ fontSize: 18, color: theme.palette.primary.main }} />
        )}
      </Box>

      {/* Bubble */}
      <Box sx={{ maxWidth: '75%', minWidth: 80 }}>
        <Paper
          elevation={0}
          sx={{
            px: 2,
            py: 1.5,
            bgcolor: isUser ? theme.palette.primary.main : '#ffffff',
            color: isUser ? '#ffffff' : 'text.primary',
            border: isUser ? 'none' : '1px solid #dadce0',
            borderRadius: isUser ? '18px 18px 4px 18px' : '4px 18px 18px 18px',
            position: 'relative',
          }}
        >
          <Typography
            variant="body1"
            component="div"
            sx={{
              fontSize: '0.875rem',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {message.content}
          </Typography>
        </Paper>

        {/* Metadata row */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mt: 0.5,
            px: 0.5,
            flexDirection: isUser ? 'row-reverse' : 'row',
          }}
        >
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.7rem' }}>
            {formatDate(message.createdAt)}
          </Typography>

          {message.latencyMs !== null && (
            <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.7rem' }}>
              · {formatLatency(message.latencyMs)}
            </Typography>
          )}

          {!isUser && (
            <Tooltip title="Copy response">
              <IconButton
                size="small"
                onClick={handleCopy}
                sx={{ p: 0.25, opacity: 0.5, '&:hover': { opacity: 1 } }}
              >
                <ContentCopyOutlined sx={{ fontSize: 13 }} />
              </IconButton>
            </Tooltip>
          )}

          {!isUser && message.sources.length > 0 && (
            <Chip
              icon={<ArticleOutlined sx={{ fontSize: '12px !important' }} />}
              label={`${message.sources.length} source${message.sources.length > 1 ? 's' : ''}`}
              size="small"
              onClick={() => setSourcesOpen((o) => !o)}
              onDelete={() => setSourcesOpen((o) => !o)}
              deleteIcon={sourcesOpen ? <ExpandLessOutlined /> : <ExpandMoreOutlined />}
              variant="outlined"
              sx={{
                height: 20,
                fontSize: '0.68rem',
                borderRadius: 1,
                cursor: 'pointer',
                borderColor: 'divider',
              }}
            />
          )}
        </Box>

        {/* Sources accordion */}
        {!isUser && message.sources.length > 0 && (
          <Collapse in={sourcesOpen}>
            <Box
              sx={{
                mt: 1,
                p: 1.5,
                bgcolor: '#f8f9fa',
                borderRadius: 2,
                border: '1px solid #dadce0',
              }}
            >
              <Typography
                variant="caption"
                sx={{ fontWeight: 600, color: 'text.secondary', mb: 1, display: 'block' }}
              >
                Retrieved sources
              </Typography>
              {message.sources.map((source, i) => (
                <Box
                  key={i}
                  sx={{
                    mb: 1,
                    pb: 1,
                    borderBottom: i < message.sources.length - 1 ? '1px solid #e8eaed' : 'none',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                    <ArticleOutlined sx={{ fontSize: 12, color: 'text.secondary' }} />
                    <Typography
                      variant="caption"
                      sx={{ fontWeight: 500, color: theme.palette.primary.main }}
                    >
                      {source.documentName}
                      {source.pageNumber && ` · p.${source.pageNumber}`}
                    </Typography>
                    <Chip
                      label={`${Math.round(source.score * 100)}%`}
                      size="small"
                      sx={{ height: 16, fontSize: '0.6rem', ml: 'auto', borderRadius: 1 }}
                    />
                  </Box>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontStyle: 'italic', lineHeight: 1.5, display: 'block' }}
                  >
                    "{source.chunkText}"
                  </Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        )}
      </Box>
    </Box>
  );
}
