import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '@/api/documents';
import { QUERY_KEYS } from '@/utils/constants';

export function useDocuments(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...QUERY_KEYS.documents, page, pageSize],
    queryFn: () => documentsApi.list(page, pageSize),
    staleTime: 30_000,
    refetchInterval: (query) => {
      const hasProcessing = query.state.data?.items.some(
        (d) => d.status === 'processing' || d.status === 'uploading',
      );
      return hasProcessing ? 5_000 : false;
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.documents });
    },
  });
}

export function useReindexDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: documentsApi.reindex,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: QUERY_KEYS.documents });
    },
  });
}
