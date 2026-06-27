import { useState } from 'react';
import { Box, Button, TextField, InputAdornment, Typography, Chip } from '@mui/material';
import { CloudUploadOutlined, SearchOutlined, RefreshOutlined } from '@mui/icons-material';
import { PageHeader } from '@/components/common/PageHeader';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { DocumentList } from '@/components/documents/DocumentList';
import { UploadDialog } from '@/components/documents/UploadDialog';
import { useDocuments, useDeleteDocument, useReindexDocument } from '@/hooks/useDocuments';

export function Documents() {
  const [uploadOpen, setUploadOpen] = useState(false);
  const [search, setSearch] = useState('');

  const { data, isLoading, error, refetch } = useDocuments();
  const deleteMutation = useDeleteDocument();
  const reindexMutation = useReindexDocument();

  const docs = data?.items ?? [];
  const filtered = docs.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase()),
  );

  const indexedCount = docs.filter((d) => d.status === 'indexed').length;
  const processingCount = docs.filter(
    (d) => d.status === 'processing' || d.status === 'uploading',
  ).length;

  return (
    <Box>
      <PageHeader
        title="Documents"
        subtitle="Manage your enterprise knowledge base"
        actions={
          <>
            <Button
              variant="outlined"
              startIcon={<RefreshOutlined />}
              onClick={() => void refetch()}
              size="small"
              color="inherit"
              sx={{ borderColor: 'divider' }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<CloudUploadOutlined />}
              onClick={() => setUploadOpen(true)}
            >
              Upload
            </Button>
          </>
        }
      />

      {/* Status chips */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2.5, flexWrap: 'wrap' }}>
        <Chip label={`${docs.length} total`} size="small" variant="outlined" />
        <Chip label={`${indexedCount} indexed`} size="small" color="success" variant="outlined" />
        {processingCount > 0 && (
          <Chip
            label={`${processingCount} processing`}
            size="small"
            color="warning"
            variant="outlined"
          />
        )}
      </Box>

      {/* Search */}
      {docs.length > 0 && (
        <TextField
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter documents by name…"
          size="small"
          sx={{ mb: 2.5, maxWidth: 400 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchOutlined sx={{ fontSize: 18, color: 'text.secondary' }} />
              </InputAdornment>
            ),
          }}
        />
      )}

      {search && filtered.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
          No documents match "{search}"
        </Typography>
      )}

      {error ? (
        <ErrorMessage
          message={(error as Error).message}
          onRetry={() => void refetch()}
        />
      ) : (
        <DocumentList
          documents={search ? filtered : docs}
          isLoading={isLoading}
          onDelete={(id) => void deleteMutation.mutateAsync(id)}
          onReindex={(id) => void reindexMutation.mutateAsync(id)}
          onUpload={() => setUploadOpen(true)}
        />
      )}

      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={() => void refetch()}
      />
    </Box>
  );
}
