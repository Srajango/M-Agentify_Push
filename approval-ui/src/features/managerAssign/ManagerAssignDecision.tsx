import { useState, type ReactElement } from 'react';
import { Link as RouterLink, useLocation, useNavigate, useParams } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select, { type SelectChangeEvent } from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { OrchestratorRequestError, resumeManagerAssign, toMessage, type ManagerAssignQueueItem } from '../../api/orchestratorClient';

/**
 * Lets the manager pick a different active agent for one queued lead and confirm;
 * confirming calls the orchestrator's resume action for `manager_manual_assign`.
 * The queued lead (including its candidate agents) is handed in via navigation
 * state from `ManagerAssignQueue` — this screen displays only what it is given.
 */
export default function ManagerAssignDecision(): ReactElement {
  const { leadId } = useParams<{ leadId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const item = location.state as ManagerAssignQueueItem | null;

  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<{ message: string; retryable: boolean } | null>(null);

  if (!item || item.leadId !== leadId) {
    return (
      <Stack spacing={2} sx={{ py: 4 }}>
        <Alert severity="warning">
          This lead is no longer in the queue. Return to the queue and select a lead to assign.
        </Alert>
        <Button component={RouterLink} to="/manager" variant="outlined">
          Back to queue
        </Button>
      </Stack>
    );
  }

  const handleConfirm = async (): Promise<void> => {
    if (!selectedAgentId) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await resumeManagerAssign(item.leadId, selectedAgentId);
      navigate('/manager');
    } catch (caught) {
      const retryable = caught instanceof OrchestratorRequestError ? caught.retryable : true;
      setError({ message: toMessage(caught), retryable });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Stack spacing={3} sx={{ py: 3, maxWidth: 480 }}>
      <Typography variant="h6">Assign agent for lead {item.leadId}</Typography>
      <Typography variant="body2" color="text.secondary">
        {item.city} — waiting since {item.requestedAt}
      </Typography>

      <FormControl fullWidth disabled={submitting}>
        <InputLabel id="agent-select-label">Active agent</InputLabel>
        <Select
          labelId="agent-select-label"
          label="Active agent"
          value={selectedAgentId}
          onChange={(event: SelectChangeEvent) => setSelectedAgentId(event.target.value)}
        >
          {item.candidateAgents.map((agent) => (
            <MenuItem key={agent.agentId} value={agent.agentId}>
              {agent.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {error ? <Alert severity="error">{error.message}{error.retryable ? ' — you can retry.' : ''}</Alert> : null}

      <Stack direction="row" spacing={2}>
        <Button
          variant="contained"
          disabled={!selectedAgentId || submitting}
          onClick={handleConfirm}
        >
          Confirm assignment
        </Button>
        <Button component={RouterLink} to="/manager" disabled={submitting}>
          Cancel
        </Button>
      </Stack>
    </Stack>
  );
}
