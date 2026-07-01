import { useCallback, useEffect, useRef, useState } from 'react';
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
  HourglassTopOutlined,
} from '@mui/icons-material';
import { useDropzone, type FileRejection } from 'react-dropzone';
import { documentsApi } from '@/api/documents';
import { formatBytes } from '@/utils/formatters';
import { MAX_UPLOAD_SIZE_BYTES } from '@/utils/constants';

const SERVICE_NOT_READY_CODE = 'SERVICE_NOT_READY';
const RETRY_DELAY_MS = 8_000;

interface FileState {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'done' | 'error' | 'retrying';
  error?: string;
  retryIn?: number;
}

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function UploadDialog({ open, onClose, onSuccess }: UploadDialogProps) {
  const [files, setFiles] = useState<FileState[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const retryTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Countdown ticker for files in 'retrying' state
  useEffect(() => {
    const hasRetrying = files.some((f) => f.status === 'retrying');
    if (!hasRetrying) return;
    const interval = setInterval(() => {
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'retrying' && f.retryIn !== undefined
            ? { ...f, retryIn: Math.max(0, f.retryIn - 1) }
            : f,
        ),
      );
    }, 1_000);
    return () => clearInterval(interval);
  }, [files]);

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

  const uploadSingleFile = useCallback(
    async (fileState: FileState): Promise<boolean> => {
      setFiles((prev) =>
        prev.map((f) => (f.file === fileState.file ? { ...f, status: 'uploading', retryIn: undefined } : f)),
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
        return true;
      } catch (err) {
        const msg = (err as Error).message;
        const isNotReady = msg.includes(SERVICE_NOT_READY_CODE) || msg.toLowerCase().includes('not yet initialised');

        if (isNotReady) {
          const delaySecs = Math.round(RETRY_DELAY_MS / 1000);
          setFiles((prev) =>
            prev.map((f) =>
              f.file === fileState.file
                ? { ...f, status: 'retrying', error: undefined, retryIn: delaySecs }
                : f,
            ),
          );
          // Auto-retry after delay
          const key = fileState.file.name + fileState.file.size;
          retryTimers.current.get(key) && clearTimeout(retryTimers.current.get(key));
          const timer = setTimeout(() => {
            void uploadSingleFile(fileState);
          }, RETRY_DELAY_MS);
          retryTimers.current.set(key, timer);
          return false;
        }

        setFiles((prev) =>
          prev.map((f) =>
            f.file === fileState.file ? { ...f, status: 'error', error: msg } : f,
          ),
        );
        return false;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const handleUpload = async () => {
    const pending = files.filter((f) => f.status === 'pending');
    if (pending.length === 0) return;

    setIsUploading(true);
    const results = await Promise.all(pending.map((fs) => uploadSingleFile(fs)));
    setIsUploading(false);

    const allDone = results.every(Boolean) && files.every((f) => f.status === 'done' || results[pending.indexOf(f)]);
    if (files.filter((f) => f.status !== 'retrying').every((f) => f.status === 'done')) {
      onSuccess();
      handleClose();
    }
    void allDone; // referenced to avoid lint warning
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

  const pendingCount = files.filter((f) => f.status === 'pending' || f.status === 'error').length;
  const retryingCount = files.filter((f) => f.status === 'retrying').length;

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
                  ) : fileState.status === 'retrying' ? (
                    <HourglassTopOutlined sx={{ color: 'warning.main', fontSize: 20 }} />
                  ) : (
                    <InsertDriveFileOutlined sx={{ color: 'primary.main', fontSize: 20 }} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={fileState.file.name}
                  secondary={
                    fileState.status === 'error'
                      ? fileState.error
                      : fileState.status === 'retrying'
                      ? `Backend starting up — retrying in ${fileState.retryIn ?? 0}s…`
                      : `${formatBytes(fileState.file.size)} · ${fileState.status}`
                  }
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                  secondaryTypographyProps={{
                    variant: 'caption',
                    color:
                      fileState.status === 'error'
                        ? 'error'
                        : fileState.status === 'retrying'
                        ? 'warning.main'
                        : 'text.secondary',
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
                {fileState.status === 'retrying' && (
                  <Box sx={{ width: 80, ml: 1 }}>
                    <LinearProgress variant="indeterminate" color="warning" sx={{ borderRadius: 2 }} />
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
        {files.some((f) => f.status === 'retrying') && !files.some((f) => f.status === 'error') && (
          <Alert severity="warning" sx={{ mt: 1, borderRadius: 2 }}>
            Backend services are starting up. Files will be uploaded automatically once ready.
          </Alert>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2.5, gap: 1 }}>
        <Button onClick={handleClose} disabled={isUploading} variant="text" color="inherit">
          Cancel
        </Button>
        <Button
          onClick={() => void handleUpload()}
          disabled={(pendingCount === 0 && retryingCount === 0) || isUploading}
          variant="contained"
          startIcon={<CloudUploadOutlined />}
        >
          {isUploading
            ? 'Uploading…'
            : retryingCount > 0 && pendingCount === 0
            ? 'Waiting for backend…'
            : `Upload ${pendingCount > 0 ? `${pendingCount} file${pendingCount > 1 ? 's' : ''}` : ''}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
