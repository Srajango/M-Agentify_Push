import { useEffect, useState } from 'react';
import { fetchHealth } from '../api/orchestratorClient';

export type OrchestratorHealthState = 'checking' | 'healthy' | 'unreachable';

/**
 * Calls the orchestrator's `GET /health` once on mount to report whether the
 * dependency this whole UI relies on is reachable, shown as a small banner by
 * the app shell. Queue and decision screens still attempt their own calls
 * regardless of this result — it is advisory, not a gate.
 */
export function useOrchestratorHealth(): OrchestratorHealthState {
  const [state, setState] = useState<OrchestratorHealthState>('checking');

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then(() => {
        if (!cancelled) {
          setState('healthy');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState('unreachable');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
