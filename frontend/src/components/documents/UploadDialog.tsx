import { useCallback, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import {
  CloudUploadOutlined,
  CloseOutlined,
  InsertDriveFileOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
} from '@mui/icons-material';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { documentsApi } from '@/api/documents';
import { formatBytes } from '@/utils/formatters';
import { MAX_UPLOAD_SIZE_BYTES } from '@/utils/constants';

interface FileState {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'done' | 'error';
  error?: string;
}

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function UploadDialog({ open, onClose, onSuccess }: UploadDialogProps) {
  const [files, setFiles] = useState<FileState[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((accepted: File[], rejected: FileRejection[]) => {
    const newFiles: FileState[] = accepted.map((f) => ({
      file: f,
      progress: 0,
      status: 'pending',
    }));

    const rejectedFiles: FileState[] = rejected.map((r) => ({
      file: r.file,
      progress: 0,
      status: 'error',
      error: r.errors.map((e: { message: string }) => e.message).join(', '),
    }));

    setFiles((prev) => [...prev, ...newFiles, ...rejectedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'text/plain': ['.txt'], 'text/markdown': ['.md'] },
    maxSize: MAX_UPLOAD_SIZE_BYTES,
    multiple: true,
  });

  const handleUpload = async () => {
    const pending = files.filter((f) => f.status === 'pending');
    if (pending.length === 0) return;

    setIsUploading(true);
    let allDone = true;

    for (const fileState of pending) {
      setFiles((prev) =>
        prev.map((f) => (f.file === fileState.file ? { ...f, status: 'uploading' } : f)),
      );

      try {
        await documentsApi.upload(fileState.file, (pct) => {
          setFiles((prev) =>
            prev.map((f) => (f.file === fileState.file ? { ...f, progress: pct } : f)),
          );
        });
        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileState.file ? { ...f, status: 'done', progress: 100 } : f,
          ),
        );
      } catch (err) {
        allDone = false;
        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileState.file
              ? { ...f, status: 'error', error: (err as Error).message }
              : f,
          ),
        );
      }
    }

    setIsUploading(false);
    if (allDone) {
      onSuccess();
      handleClose();
    }
  };

  const handleClose = () => {
    if (!isUploading) {
      setFiles([]);
      onClose();
    }
  };

  const removeFile = (file: File) => {
    setFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const pendingCount = files.filter((f) => f.status === 'pending').length;

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{ sx: { borderRadius: 3 } }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Typography variant="h6" fontWeight={500}>
          Upload Documents
        </Typography>
        <IconButton onClick={handleClose} disabled={isUploading} size="small">
          <CloseOutlined />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pb: 1 }}>
        {/* Drop zone */}
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'divider',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'rgba(26,115,232,0.04)' : 'background.default',
            transition: 'all 0.15s ease',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'rgba(26,115,232,0.04)',
            },
            mb: files.length > 0 ? 2 : 0,
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadOutlined sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
          <Typography variant="body1" fontWeight={500} gutterBottom>
            {isDragActive ? 'Drop files here' : 'Drag & drop files, or click to browse'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            PDF, TXT, Markdown · Max {MAX_UPLOAD_SIZE_BYTES / 1024 / 1024}MB per file
          </Typography>
        </Box>

        {/* File list */}
        {files.length > 0 && (
          <List dense disablePadding>
            {files.map((fileState, i) => (
              <ListItem
                key={i}
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1.5,
                  mb: 0.75,
                  pr: 1,
                }}
                secondaryAction={
                  fileState.status !== 'uploading' && (
                    <IconButton
                      size="small"
                      onClick={() => removeFile(fileState.file)}
                      sx={{ opacity: 0.5, '&:hover': { opacity: 1 } }}
                    >
                      <CloseOutlined sx={{ fontSize: 14 }} />
                    </IconButton>
                  )
                }
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {fileState.status === 'done' ? (
                    <CheckCircleOutlined sx={{ color: 'success.main', fontSize: 20 }} />
                  ) : fileState.status === 'error' ? (
                    <ErrorOutlined sx={{ color: 'error.main', fontSize: 20 }} />
                  ) : (
                    <InsertDriveFileOutlined sx={{ color: 'primary.main', fontSize: 20 }} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={fileState.file.name}
                  secondary={
                    fileState.status === 'error'
                      ? fileState.error
                      : `${formatBytes(fileState.file.size)} · ${fileState.status}`
                  }
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                  secondaryTypographyProps={{
                    variant: 'caption',
                    color: fileState.status === 'error' ? 'error' : 'text.secondary',
                  }}
                />
                {fileState.status === 'uploading' && (
                  <Box sx={{ width: 80, ml: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={fileState.progress}
                      sx={{ borderRadius: 2 }}
                    />
                  </Box>
                )}
              </ListItem>
            ))}
          </List>
        )}

        {files.some((f) => f.status === 'error') && (
          <Alert severity="error" sx={{ mt: 1, borderRadius: 2 }}>
            Some files failed to upload. Remove them or retry.
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2.5, gap: 1 }}>
        <Button onClick={handleClose} disabled={isUploading} variant="text" color="inherit">
          Cancel
        </Button>
        <Button
          onClick={() => void handleUpload()}
          disabled={pendingCount === 0 || isUploading}
          variant="contained"
          startIcon={<CloudUploadOutlined />}
        >
          {isUploading
            ? 'Uploading…'
            : `Upload ${pendingCount > 0 ? `${pendingCount} file${pendingCount > 1 ? 's' : ''}` : ''}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
