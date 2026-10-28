import type { ReactElement } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

/** Centered spinner shown while a queue is being fetched. */
export function LoadingState({ label }: { label: string }): ReactElement {
  return (
    <Stack alignItems="center" spacing={2} sx={{ py: 6 }}>
      <CircularProgress aria-label={label} />
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Stack>
  );
}

/** Error banner with a retry action, used for both queue loads and gate submissions. */
export function ErrorState({
  message,
  retryable,
  onRetry,
}: {
  message: string;
  retryable: boolean;
  onRetry: () => void;
}): ReactElement {
  return (
    <Box sx={{ py: 2 }}>
      <Alert severity="error" action={retryable ? <Button color="inherit" size="small" onClick={onRetry}>Retry</Button> : undefined}>
        {message}
      </Alert>
    </Box>
  );
}

/** Explicit "nothing waiting" message so an empty queue never renders a blank list. */
export function EmptyState({ message }: { message: string }): ReactElement {
  return (
    <Box sx={{ py: 6, textAlign: 'center' }}>
      <Typography variant="body1" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
