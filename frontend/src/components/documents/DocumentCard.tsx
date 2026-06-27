import {
  Card,
  CardContent,
  CardActions,
  Box,
  Typography,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  PictureAsPdfOutlined,
  TextSnippetOutlined,
  DeleteOutlined,
  RefreshOutlined,
  LayersOutlined,
} from '@mui/icons-material';
import type { Document } from '@/types';
import { StatusChip } from '@/components/common/StatusChip';
import { formatBytes, formatRelativeTime } from '@/utils/formatters';

const MIME_ICONS: Record<string, typeof PictureAsPdfOutlined> = {
  'application/pdf': PictureAsPdfOutlined,
  'text/plain': TextSnippetOutlined,
  'text/markdown': TextSnippetOutlined,
};

interface DocumentCardProps {
  document: Document;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
}

export function DocumentCard({ document, onDelete, onReindex }: DocumentCardProps) {
  const Icon = MIME_ICONS[document.mimeType] ?? TextSnippetOutlined;
  const isProcessing = document.status === 'processing' || document.status === 'uploading';

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.15s ease',
      }}
    >
      {isProcessing && <LinearProgress sx={{ borderRadius: '8px 8px 0 0' }} />}

      <CardContent sx={{ flex: 1, pb: 1 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.5, mb: 1.5 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 1.5,
              bgcolor: 'rgba(26,115,232,0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <Icon sx={{ fontSize: 22, color: 'primary.main' }} />
          </Box>
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Tooltip title={document.name}>
              <Typography
                variant="body2"
                fontWeight={500}
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  mb: 0.5,
                }}
              >
                {document.name}
              </Typography>
            </Tooltip>
            <StatusChip status={document.status} />
          </Box>
        </Box>

        {/* Stats */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              Size
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {formatBytes(document.size)}
            </Typography>
          </Box>
          {document.chunkCount > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" display="block">
                Chunks
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <LayersOutlined sx={{ fontSize: 12, color: 'text.secondary' }} />
                <Typography variant="body2" fontWeight={500}>
                  {document.chunkCount}
                </Typography>
              </Box>
            </Box>
          )}
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              Uploaded
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {formatRelativeTime(document.uploadedAt)}
            </Typography>
          </Box>
        </Box>

        {document.errorMessage && (
          <Typography
            variant="caption"
            color="error"
            sx={{ display: 'block', mt: 1, fontSize: '0.7rem' }}
          >
            {document.errorMessage}
          </Typography>
        )}
      </CardContent>

      <CardActions sx={{ px: 2, pb: 1.5, pt: 0, justifyContent: 'flex-end', gap: 0.5 }}>
        {document.status === 'failed' && (
          <Tooltip title="Re-index document">
            <IconButton
              size="small"
              onClick={() => onReindex(document.id)}
              color="primary"
            >
              <RefreshOutlined sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="Delete document">
          <IconButton
            size="small"
            onClick={() => onDelete(document.id)}
            color="error"
            disabled={isProcessing}
          >
            <DeleteOutlined sx={{ fontSize: 18 }} />
          </IconButton>
        </Tooltip>
      </CardActions>
    </Card>
  );
}
