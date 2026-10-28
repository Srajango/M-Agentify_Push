import { useCallback, useEffect, useState } from 'react';
import {
  OrchestratorRequestError,
  fetchReferralQueue,
  toMessage,
  type ReferralQueueItem,
} from '../../api/orchestratorClient';

export type ReferralQueueState =
  | { status: 'loading' }
  | { status: 'error'; message: string; retryable: boolean }
  | { status: 'empty' }
  | { status: 'ready'; items: ReferralQueueItem[] };

/** Owns loading/error/empty/data for the underwriter referral queue fetch. */
export function useReferralQueue(): { state: ReferralQueueState; reload: () => void } {
  const [state, setState] = useState<ReferralQueueState>({ status: 'loading' });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });
    fetchReferralQueue()
      .then((items) => {
        if (cancelled) {
          return;
        }
        setState(items.length === 0 ? { status: 'empty' } : { status: 'ready', items });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const retryable = error instanceof OrchestratorRequestError ? error.retryable : true;
        setState({ status: 'error', message: toMessage(error), retryable });
      });
    return () => {
      cancelled = true;
    };
  }, [version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { state, reload };
}
