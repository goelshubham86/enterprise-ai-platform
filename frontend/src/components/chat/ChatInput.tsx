import { useRef, useEffect, type KeyboardEvent } from 'react';
import {
  Box,
  IconButton,
  TextField,
  Tooltip,
  Typography,
  CircularProgress,
  Paper,
} from '@mui/material';
import { SendOutlined, StopOutlined, AttachFileOutlined } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({
  question: z.string().min(1).max(4000),
});

type FormValues = z.infer<typeof schema>;

interface ChatInputProps {
  onSend: (question: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isValid },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { question: '' },
    mode: 'onChange',
  });

  useEffect(() => {
    if (!isLoading) {
      textareaRef.current?.focus();
    }
  }, [isLoading]);

  const onSubmit = (values: FormValues) => {
    onSend(values.question.trim());
    reset();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(onSubmit)();
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 3,
        bgcolor: 'background.paper',
        '&:focus-within': {
          borderColor: 'primary.main',
          boxShadow: '0 0 0 2px rgba(26,115,232,0.12)',
        },
        transition: 'all 0.15s ease',
      }}
    >
      <Box sx={{ px: 1.5, pt: 1 }}>
        <Controller
          name="question"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              inputRef={textareaRef}
              multiline
              minRows={1}
              maxRows={8}
              fullWidth
              placeholder="Ask a question about your documents… (Shift+Enter for new line)"
              disabled={disabled || isLoading}
              onKeyDown={handleKeyDown}
              variant="standard"
              InputProps={{ disableUnderline: true }}
              sx={{
                '& .MuiInputBase-root': {
                  fontSize: '0.9rem',
                  lineHeight: 1.6,
                  py: 0.5,
                },
              }}
            />
          )}
        />
      </Box>

      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 1.5,
          pb: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title="Attach document (coming soon)">
            <span>
              <IconButton size="small" disabled sx={{ opacity: 0.4 }}>
                <AttachFileOutlined sx={{ fontSize: 18 }} />
              </IconButton>
            </span>
          </Tooltip>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.7rem' }}>
            Powered by Gemini · RAG
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="caption" color="text.disabled" sx={{ fontSize: '0.7rem' }}>
            Enter to send
          </Typography>
          <Tooltip title={isLoading ? 'Stop generation' : 'Send message'}>
            <span>
              <IconButton
                size="small"
                color="primary"
                onClick={isLoading ? undefined : () => void handleSubmit(onSubmit)()}
                disabled={(!isValid && !isLoading) || disabled}
                sx={{
                  bgcolor: isValid || isLoading ? 'primary.main' : 'action.disabledBackground',
                  color: '#fff',
                  width: 32,
                  height: 32,
                  '&:hover': { bgcolor: 'primary.dark' },
                  '&.Mui-disabled': { bgcolor: 'action.disabledBackground', color: 'action.disabled' },
                }}
              >
                {isLoading ? (
                  <CircularProgress size={16} sx={{ color: '#fff' }} />
                ) : isLoading ? (
                  <StopOutlined sx={{ fontSize: 18 }} />
                ) : (
                  <SendOutlined sx={{ fontSize: 16 }} />
                )}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </Box>
    </Paper>
  );
}
