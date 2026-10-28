import type { ReactElement } from 'react';
import { useNavigate } from 'react-router-dom';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { EmptyState, ErrorState, LoadingState } from '../../components/QueueStates';
import { useManagerAssignQueue } from './useManagerAssignQueue';

/**
 * Lists every lead paused at the `manager_manual_assign` gate because no active
 * agent covers its city. Selecting a row opens the Assign Agent Decision screen.
 */
export default function ManagerAssignQueue(): ReactElement {
  const { state, reload } = useManagerAssignQueue();
  const navigate = useNavigate();

  if (state.status === 'loading') {
    return <LoadingState label="Loading leads waiting for manual assignment" />;
  }
  if (state.status === 'error') {
    return <ErrorState message={state.message} retryable={state.retryable} onRetry={reload} />;
  }
  if (state.status === 'empty') {
    return <EmptyState message="No leads are waiting for manual assignment." />;
  }

  return (
    <List aria-label="Manager assignment queue">
      {state.items.map((item) => (
        <ListItemButton
          key={item.leadId}
          onClick={() => navigate(`/manager/${item.leadId}`, { state: item })}
        >
          <ListItemText
            primary={`Lead ${item.leadId} — ${item.city}`}
            secondary={
              <Typography component="span" variant="body2" color="text.secondary">
                Waiting since {item.requestedAt}
              </Typography>
            }
          />
        </ListItemButton>
      ))}
    </List>
  );
}
