import type { HealthStatus } from '@/types';
import { apiClient } from './client';

export const healthApi = {
  check: async (): Promise<HealthStatus> => {
    const { data } = await apiClient.get<HealthStatus>('/health');
    return data;
  },
};
