import {
  Box,
  Card,
  CardContent,
  Typography,
  Divider,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Alert,
  Grid,
  Chip,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { SaveOutlined } from '@mui/icons-material';
import { PageHeader } from '@/components/common/PageHeader';

const schema = z.object({
  modelId: z.string().min(1, 'Model ID is required'),
  temperature: z.coerce.number().min(0).max(1),
  maxOutputTokens: z.coerce.number().int().min(256).max(8192),
  chunkSize: z.coerce.number().int().min(128).max(2048),
  chunkOverlap: z.coerce.number().int().min(0).max(512),
  topK: z.coerce.number().int().min(1).max(20),
  streamResponses: z.boolean(),
  logQueries: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

const DEFAULT_VALUES: FormValues = {
  modelId: 'gemini-1.5-pro-002',
  temperature: 0.2,
  maxOutputTokens: 2048,
  chunkSize: 512,
  chunkOverlap: 64,
  topK: 5,
  streamResponses: false,
  logQueries: true,
};

interface SettingRowProps {
  label: string;
  description?: string;
  control: React.ReactNode;
}

function SettingRow({ label, description, control }: SettingRowProps) {
  return (
    <>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          py: 2,
          gap: 2,
        }}
      >
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" fontWeight={500}>
            {label}
          </Typography>
          {description && (
            <Typography variant="caption" color="text.secondary">
              {description}
            </Typography>
          )}
        </Box>
        <Box sx={{ flexShrink: 0 }}>{control}</Box>
      </Box>
      <Divider />
    </>
  );
}

export function Settings() {
  const {
    control,
    handleSubmit,
    formState: { isDirty, isSubmitting },
    reset,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: DEFAULT_VALUES,
  });

  const onSubmit = async (values: FormValues) => {
    // Settings are stored in backend — placeholder for now
    await new Promise((r) => setTimeout(r, 800));
    reset(values);
    console.log('Settings saved:', values);
  };

  return (
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Configure AI model parameters and platform behavior"
        actions={
          <Button
            variant="contained"
            startIcon={<SaveOutlined />}
            onClick={() => void handleSubmit(onSubmit)()}
            disabled={!isDirty || isSubmitting}
          >
            {isSubmitting ? 'Saving…' : 'Save Changes'}
          </Button>
        }
      />

      <Alert severity="info" sx={{ mb: 3, borderRadius: 2 }}>
        Settings are applied to new chat sessions. Active sessions retain their configuration.
      </Alert>

      <Grid container spacing={2}>
        {/* AI Model */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="h5">AI Model</Typography>
                <Chip label="Vertex AI" size="small" color="primary" variant="outlined" sx={{ borderRadius: 1 }} />
              </Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Vertex AI Gemini model configuration
              </Typography>

              <SettingRow
                label="Model ID"
                description="Vertex AI model identifier"
                control={
                  <Controller
                    name="modelId"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        sx={{ width: 240 }}
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Temperature"
                description="Controls randomness (0 = deterministic, 1 = creative)"
                control={
                  <Controller
                    name="temperature"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        type="number"
                        inputProps={{ min: 0, max: 1, step: 0.05 }}
                        sx={{ width: 100 }}
                        error={!!fieldState.error}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Max Output Tokens"
                description="Maximum tokens in the model response"
                control={
                  <Controller
                    name="maxOutputTokens"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        type="number"
                        inputProps={{ min: 256, max: 8192, step: 256 }}
                        sx={{ width: 100 }}
                        error={!!fieldState.error}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Stream Responses"
                description="Enable token streaming (WebSocket)"
                control={
                  <Controller
                    name="streamResponses"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} size="small" />}
                        label=""
                        sx={{ m: 0 }}
                      />
                    )}
                  />
                }
              />
            </CardContent>
          </Card>
        </Grid>

        {/* RAG Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="h5">RAG Pipeline</Typography>
                <Chip label="Vector Search" size="small" color="secondary" variant="outlined" sx={{ borderRadius: 1 }} />
              </Box>
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Retrieval-Augmented Generation parameters
              </Typography>

              <SettingRow
                label="Chunk Size"
                description="Tokens per document chunk (affects retrieval granularity)"
                control={
                  <Controller
                    name="chunkSize"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        type="number"
                        inputProps={{ min: 128, max: 2048, step: 64 }}
                        sx={{ width: 100 }}
                        error={!!fieldState.error}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Chunk Overlap"
                description="Token overlap between consecutive chunks"
                control={
                  <Controller
                    name="chunkOverlap"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        type="number"
                        inputProps={{ min: 0, max: 512, step: 16 }}
                        sx={{ width: 100 }}
                        error={!!fieldState.error}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Top-K Results"
                description="Number of chunks retrieved per query"
                control={
                  <Controller
                    name="topK"
                    control={control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        size="small"
                        type="number"
                        inputProps={{ min: 1, max: 20 }}
                        sx={{ width: 100 }}
                        error={!!fieldState.error}
                      />
                    )}
                  />
                }
              />

              <SettingRow
                label="Log Queries"
                description="Store queries in BigQuery for analytics"
                control={
                  <Controller
                    name="logQueries"
                    control={control}
                    render={({ field }) => (
                      <FormControlLabel
                        control={<Switch {...field} checked={field.value} size="small" />}
                        label=""
                        sx={{ m: 0 }}
                      />
                    )}
                  />
                }
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
