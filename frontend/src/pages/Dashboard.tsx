import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
} from '@mui/material';
import {
  FolderOutlined,
  ChatOutlined,
  CheckCircleOutlined,
  AutoAwesomeOutlined,
  TrendingUpOutlined,
  CloudUploadOutlined,
  ArrowForwardOutlined,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusChip } from '@/components/common/StatusChip';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useDocuments } from '@/hooks/useDocuments';
import { useHealth } from '@/hooks/useHealth';
import { ROUTES } from '@/utils/constants';
import { formatRelativeTime, formatBytes } from '@/utils/formatters';

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
}

function StatCard({ label, value, sub, icon, color, onClick }: StatCardProps) {
  return (
    <Card
      onClick={onClick}
      sx={{ cursor: onClick ? 'pointer' : 'default', transition: 'all 0.15s ease' }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="caption" color="text.secondary" fontWeight={500}>
              {label}
            </Typography>
            <Typography variant="h3" fontWeight={600} sx={{ my: 0.5 }}>
              {value}
            </Typography>
            {sub && (
              <Typography variant="caption" color="text.secondary">
                {sub}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2,
              bgcolor: `${color}18`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Box sx={{ color }}>{icon}</Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const navigate = useNavigate();
  const { data: docsData, isLoading: docsLoading } = useDocuments();
  const { data: health } = useHealth();

  const docs = docsData?.items ?? [];
  const indexedCount = docs.filter((d) => d.status === 'indexed').length;
  const processingCount = docs.filter(
    (d) => d.status === 'processing' || d.status === 'uploading',
  ).length;
  const totalChunks = docs.reduce((sum, d) => sum + d.chunkCount, 0);
  const recentDocs = [...docs]
    .sort((a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime())
    .slice(0, 5);

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of your Enterprise AI Knowledge Assistant"
        actions={
          <Button
            variant="contained"
            startIcon={<CloudUploadOutlined />}
            onClick={() => navigate(ROUTES.documents)}
          >
            Upload Documents
          </Button>
        }
      />

      {/* System health banner */}
      {health && health.status !== 'healthy' && (
        <Alert
          severity={health.status === 'degraded' ? 'warning' : 'error'}
          sx={{ mb: 3, borderRadius: 2 }}
          action={
            <Button size="small" onClick={() => navigate(ROUTES.health)}>
              View Health
            </Button>
          }
        >
          System is {health.status}. Some services may be impacted.
        </Alert>
      )}

      {/* Stats row */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Total Documents"
            value={docs.length}
            sub={`${indexedCount} indexed`}
            icon={<FolderOutlined />}
            color="#1a73e8"
            onClick={() => navigate(ROUTES.documents)}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Vector Chunks"
            value={totalChunks.toLocaleString()}
            sub="searchable embeddings"
            icon={<TrendingUpOutlined />}
            color="#00897b"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="Processing"
            value={processingCount}
            sub={processingCount > 0 ? 'in pipeline' : 'queue empty'}
            icon={<AutoAwesomeOutlined />}
            color="#f9ab00"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            label="System Status"
            value={health ? health.status.charAt(0).toUpperCase() + health.status.slice(1) : '—'}
            sub={health ? `v${health.version}` : 'checking…'}
            icon={<CheckCircleOutlined />}
            color={health?.status === 'healthy' ? '#34a853' : '#d93025'}
            onClick={() => navigate(ROUTES.health)}
          />
        </Grid>
      </Grid>

      {/* Main content */}
      <Grid container spacing={2}>
        {/* Recent documents */}
        <Grid item xs={12} md={7}>
          <Card>
            <CardContent>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 2,
                }}
              >
                <Typography variant="h5">Recent Documents</Typography>
                <Button
                  size="small"
                  endIcon={<ArrowForwardOutlined />}
                  onClick={() => navigate(ROUTES.documents)}
                >
                  View all
                </Button>
              </Box>

              {docsLoading ? (
                <LoadingSpinner />
              ) : recentDocs.length === 0 ? (
                <Box sx={{ py: 4, textAlign: 'center' }}>
                  <FolderOutlined sx={{ fontSize: 40, color: 'text.disabled', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    No documents yet. Upload your first document to get started.
                  </Typography>
                </Box>
              ) : (
                <List disablePadding>
                  {recentDocs.map((doc, i) => (
                    <Box key={doc.id}>
                      <ListItem disablePadding sx={{ py: 1 }}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <FolderOutlined sx={{ fontSize: 18, color: 'primary.main' }} />
                        </ListItemIcon>
                        <ListItemText
                          primary={doc.name}
                          secondary={`${formatBytes(doc.size)} · ${formatRelativeTime(doc.uploadedAt)}`}
                          primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                        <StatusChip status={doc.status} />
                      </ListItem>
                      {i < recentDocs.length - 1 && <Divider />}
                    </Box>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick actions + RAG platform info */}
        <Grid item xs={12} md={5}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<ChatOutlined />}
                  onClick={() => navigate(ROUTES.chat)}
                  sx={{ justifyContent: 'flex-start', py: 1.25 }}
                >
                  Start a new chat session
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<CloudUploadOutlined />}
                  onClick={() => navigate(ROUTES.documents)}
                  sx={{ justifyContent: 'flex-start', py: 1.25 }}
                >
                  Upload documents
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Platform Capabilities
              </Typography>
              {[
                { label: 'Vertex AI Gemini', status: 'Active' },
                { label: 'RAG Pipeline', status: 'Active' },
                { label: 'Vector Embeddings', status: 'Active' },
                { label: 'AI Agents (LangGraph)', status: 'Coming soon' },
                { label: 'MCP Protocol', status: 'Coming soon' },
                { label: 'Multi-Agent Workflows', status: 'Roadmap' },
              ].map((item) => (
                <Box
                  key={item.label}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    py: 0.75,
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    '&:last-child': { borderBottom: 'none' },
                  }}
                >
                  <Typography variant="body2">{item.label}</Typography>
                  <Chip
                    label={item.status}
                    size="small"
                    color={item.status === 'Active' ? 'success' : 'default'}
                    variant={item.status === 'Active' ? 'outlined' : 'filled'}
                    sx={{ fontSize: '0.65rem', height: 20, borderRadius: 1 }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
