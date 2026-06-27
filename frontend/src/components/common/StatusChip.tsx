import { Chip, type ChipProps } from '@mui/material';
import type { DocumentStatus, ServiceStatus } from '@/types';

type Status = DocumentStatus | ServiceStatus;

const STATUS_CONFIG: Record<Status, { label: string; color: ChipProps['color'] }> = {
  uploading: { label: 'Uploading', color: 'info' },
  processing: { label: 'Processing', color: 'warning' },
  indexed: { label: 'Indexed', color: 'success' },
  failed: { label: 'Failed', color: 'error' },
  healthy: { label: 'Healthy', color: 'success' },
  degraded: { label: 'Degraded', color: 'warning' },
  unhealthy: { label: 'Unhealthy', color: 'error' },
};

interface StatusChipProps {
  status: Status;
  size?: ChipProps['size'];
}

export function StatusChip({ status, size = 'small' }: StatusChipProps) {
  const config = STATUS_CONFIG[status] ?? { label: status, color: 'default' as const };
  return (
    <Chip
      label={config.label}
      color={config.color}
      size={size}
      variant="outlined"
      sx={{ borderRadius: 1, fontWeight: 500, fontSize: '0.7rem' }}
    />
  );
}
