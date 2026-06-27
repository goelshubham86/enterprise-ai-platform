import { Box, Grid, Typography, Button } from '@mui/material';
import { FolderOpenOutlined, CloudUploadOutlined } from '@mui/icons-material';
import { DocumentCard } from './DocumentCard';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import type { Document } from '@/types';

interface DocumentListProps {
  documents: Document[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
  onUpload: () => void;
}

function EmptyState({ onUpload }: { onUpload: () => void }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 10,
        textAlign: 'center',
      }}
    >
      <FolderOpenOutlined sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
      <Typography variant="h6" fontWeight={400} gutterBottom color="text.secondary">
        No documents indexed
      </Typography>
      <Typography variant="body2" color="text.disabled" sx={{ mb: 3, maxWidth: 360 }}>
        Upload PDF, TXT, or Markdown files to build your knowledge base. Documents will be
        chunked, embedded, and indexed for RAG queries.
      </Typography>
      <Button
        variant="contained"
        startIcon={<CloudUploadOutlined />}
        onClick={onUpload}
      >
        Upload your first document
      </Button>
    </Box>
  );
}

export function DocumentList({
  documents,
  isLoading,
  onDelete,
  onReindex,
  onUpload,
}: DocumentListProps) {
  if (isLoading) {
    return <LoadingSpinner message="Loading documents…" />;
  }

  if (documents.length === 0) {
    return <EmptyState onUpload={onUpload} />;
  }

  return (
    <Grid container spacing={2}>
      {documents.map((doc) => (
        <Grid item key={doc.id} xs={12} sm={6} md={4} lg={3}>
          <DocumentCard document={doc} onDelete={onDelete} onReindex={onReindex} />
        </Grid>
      ))}
    </Grid>
  );
}
