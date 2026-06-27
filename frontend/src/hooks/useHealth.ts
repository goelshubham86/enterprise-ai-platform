import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/api/health';
import { QUERY_KEYS } from '@/utils/constants';

export function useHealth() {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: healthApi.check,
    refetchInterval: 30_000,
    retry: 1,
  });
}
