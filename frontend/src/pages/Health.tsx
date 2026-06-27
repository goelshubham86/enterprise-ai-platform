import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Divider,
  Button,
  Alert,
} from '@mui/material';
import {
  CheckCircleOutlined,
  ErrorOutlined,
  WarningAmberOutlined,
  RefreshOutlined,
  AccessTimeOutlined,
} from '@mui/icons-material';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { useHealth } from '@/hooks/useHealth';
import { formatDate, formatLatency } from '@/utils/formatters';
import type { ServiceHealth, ServiceStatus } from '@/types';

const STATUS_ICONS: Record<ServiceStatus, React.ReactNode> = {
  healthy: <CheckCircleOutlined sx={{ color: 'success.main', fontSize: 20 }} />,
  degraded: <WarningAmberOutlined sx={{ color: 'warning.main', fontSize: 20 }} />,
  unhealthy: <ErrorOutlined sx={{ color: 'error.main', fontSize: 20 }} />,
};

const STATUS_COLORS: Record<ServiceStatus, 'success' | 'warning' | 'error'> = {
  healthy: 'success',
  degraded: 'warning',
  unhealthy: 'error',
};

function ServiceRow({ service }: { service: ServiceHealth }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        py: 1.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:last-child': { borderBottom: 'none' },
      }}
    >
      {STATUS_ICONS[service.status]}
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" fontWeight={500}>
          {service.name}
        </Typography>
        {service.details && (
          <Typography variant="caption" color="text.secondary">
            {service.details}
          </Typography>
        )}
      </Box>
      {service.latencyMs !== null && (
        <Typography variant="caption" color="text.secondary">
          {formatLatency(service.latencyMs)}
        </Typography>
      )}
      <Chip
        label={service.status}
        size="small"
        color={STATUS_COLORS[service.status]}
        variant="outlined"
        sx={{ fontSize: '0.68rem', borderRadius: 1, minWidth: 80, textAlign: 'center' }}
      />
    </Box>
  );
}

export function Health() {
  const { data: health, isLoading, error, refetch, dataUpdatedAt } = useHealth();

  return (
    <Box>
      <PageHeader
        title="System Health"
        subtitle="Real-time status of all platform services"
        actions={
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={() => void refetch()}
            color="inherit"
            size="small"
            sx={{ borderColor: 'divider' }}
          >
            Refresh
          </Button>
        }
      />

      {isLoading && <LoadingSpinner message="Checking service health…" />}

      {error && (
        <ErrorMessage
          title="Health check failed"
          message={(error as Error).message}
          onRetry={() => void refetch()}
        />
      )}

      {health && (
        <>
          {/* Overall status banner */}
          <Alert
            severity={STATUS_COLORS[health.status]}
            icon={STATUS_ICONS[health.status]}
            sx={{ mb: 3, borderRadius: 2 }}
          >
            <Typography variant="body2" fontWeight={500}>
              All systems{' '}
              {health.status === 'healthy' ? 'operational' : health.status} · Version{' '}
              {health.version} · {health.environment}
            </Typography>
          </Alert>

          <Grid container spacing={2}>
            {/* Services */}
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h5" gutterBottom>
                    Services
                  </Typography>
                  {health.services.map((s) => (
                    <ServiceRow key={s.name} service={s} />
                  ))}
                  {health.services.length === 0 && (
                    <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                      No services reported
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Platform metadata */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h5" gutterBottom>
                    Platform Info
                  </Typography>

                  {[
                    {
                      label: 'Status',
                      value: (
                        <Chip
                          label={health.status}
                          size="small"
                          color={STATUS_COLORS[health.status]}
                          variant="outlined"
                          sx={{ borderRadius: 1 }}
                        />
                      ),
                    },
                    { label: 'Version', value: health.version },
                    { label: 'Environment', value: health.environment },
                    {
                      label: 'Uptime',
                      value: `${Math.floor(health.uptime / 3600)}h ${Math.floor((health.uptime % 3600) / 60)}m`,
                    },
                    {
                      label: 'Last checked',
                      value: formatDate(health.checkedAt),
                    },
                  ].map((row, i, arr) => (
                    <Box key={row.label}>
                      <Box
                        sx={{ display: 'flex', justifyContent: 'space-between', py: 1.25, alignItems: 'center' }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          {row.label}
                        </Typography>
                        {typeof row.value === 'string' ? (
                          <Typography variant="body2" fontWeight={500}>
                            {row.value}
                          </Typography>
                        ) : (
                          row.value
                        )}
                      </Box>
                      {i < arr.length - 1 && <Divider />}
                    </Box>
                  ))}
                </CardContent>
              </Card>

              {dataUpdatedAt > 0 && (
                <Box
                  sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1.5, px: 0.5 }}
                >
                  <AccessTimeOutlined sx={{ fontSize: 14, color: 'text.disabled' }} />
                  <Typography variant="caption" color="text.disabled">
                    Auto-refreshes every 30s
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
}
