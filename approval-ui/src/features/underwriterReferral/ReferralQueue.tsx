import type { ReactElement } from 'react';
import { useNavigate } from 'react-router-dom';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { EmptyState, ErrorState, LoadingState } from '../../components/QueueStates';
import { useReferralQueue } from './useReferralQueue';

/**
 * Lists every risk paused at the `underwriter_review_referral` gate awaiting an
 * underwriter decision. Selecting a row opens the Referral Decision screen.
 */
export default function ReferralQueue(): ReactElement {
  const { state, reload } = useReferralQueue();
  const navigate = useNavigate();

  if (state.status === 'loading') {
    return <LoadingState label="Loading risks waiting for a referral decision" />;
  }
  if (state.status === 'error') {
    return <ErrorState message={state.message} retryable={state.retryable} onRetry={reload} />;
  }
  if (state.status === 'empty') {
    return <EmptyState message="No risks are waiting for a referral decision." />;
  }

  return (
    <List aria-label="Underwriter referral queue">
      {state.items.map((item) => (
        <ListItemButton
          key={item.riskId}
          onClick={() => navigate(`/underwriter/${item.riskId}`, { state: item })}
        >
          <ListItemText
            primary={`Risk ${item.riskId} — ${item.applicantName}`}
            secondary={
              <Typography component="span" variant="body2" color="text.secondary">
                Referred {item.referredAt}: {item.referralReason}
              </Typography>
            }
          />
        </ListItemButton>
      ))}
    </List>
  );
}
