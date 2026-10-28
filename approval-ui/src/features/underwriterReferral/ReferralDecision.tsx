import { useState, type ReactElement } from 'react';
import { Link as RouterLink, useLocation, useNavigate, useParams } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import {
  OrchestratorRequestError,
  rejectReferral,
  resumeReferral,
  toMessage,
  type ReferralDecisionKind,
  type ReferralQueueItem,
} from '../../api/orchestratorClient';

type PendingAction = ReferralDecisionKind | 'decline' | null;

/**
 * Lets the underwriter choose Approve, Approve with loading, or Decline for one
 * queued risk and confirm. Approve and Approve with loading call the
 * orchestrator's resume action for `underwriter_review_referral`; Decline calls
 * its reject action. The queued risk is handed in via navigation state from
 * `ReferralQueue` — this screen displays only what it is given.
 */
export default function ReferralDecision(): ReactElement {
  const { riskId } = useParams<{ riskId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const item = location.state as ReferralQueueItem | null;

  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [error, setError] = useState<{ message: string; retryable: boolean } | null>(null);

  if (!item || item.riskId !== riskId) {
    return (
      <Stack spacing={2} sx={{ py: 4 }}>
        <Alert severity="warning">
          This risk is no longer in the queue. Return to the queue and select a risk to decide.
        </Alert>
        <Button component={RouterLink} to="/underwriter" variant="outlined">
          Back to queue
        </Button>
      </Stack>
    );
  }

  const submitting = pendingAction !== null;

  const handleApprove = async (decision: ReferralDecisionKind): Promise<void> => {
    setPendingAction(decision);
    setError(null);
    try {
      await resumeReferral(item.riskId, decision);
      navigate('/underwriter');
    } catch (caught) {
      const retryable = caught instanceof OrchestratorRequestError ? caught.retryable : true;
      setError({ message: toMessage(caught), retryable });
    } finally {
      setPendingAction(null);
    }
  };

  const handleDecline = async (): Promise<void> => {
    setPendingAction('decline');
    setError(null);
    try {
      await rejectReferral(item.riskId);
      navigate('/underwriter');
    } catch (caught) {
      const retryable = caught instanceof OrchestratorRequestError ? caught.retryable : true;
      setError({ message: toMessage(caught), retryable });
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <Stack spacing={3} sx={{ py: 3, maxWidth: 480 }}>
      <Typography variant="h6">Referral decision for risk {item.riskId}</Typography>
      <Typography variant="body2" color="text.secondary">
        {item.applicantName} — referred {item.referredAt}: {item.referralReason}
      </Typography>

      {error ? <Alert severity="error">{error.message}{error.retryable ? ' — you can retry.' : ''}</Alert> : null}

      <Stack direction="row" spacing={2} flexWrap="wrap">
        <Button variant="contained" disabled={submitting} onClick={() => handleApprove('approve')}>
          Approve
        </Button>
        <Button variant="outlined" disabled={submitting} onClick={() => handleApprove('approve_with_loading')}>
          Approve with loading
        </Button>
        <Button color="error" variant="outlined" disabled={submitting} onClick={handleDecline}>
          Decline
        </Button>
        <Button component={RouterLink} to="/underwriter" disabled={submitting}>
          Cancel
        </Button>
      </Stack>
    </Stack>
  );
}
