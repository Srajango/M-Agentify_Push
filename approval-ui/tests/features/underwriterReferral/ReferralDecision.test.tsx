import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReferralDecision from '../../../src/features/underwriterReferral/ReferralDecision';
import { OrchestratorRequestError, type ReferralQueueItem } from '../../../src/api/orchestratorClient';

vi.mock('../../../src/api/orchestratorClient', async () => {
  const actual = await vi.importActual<typeof import('../../../src/api/orchestratorClient')>(
    '../../../src/api/orchestratorClient',
  );
  return {
    ...actual,
    resumeReferral: vi.fn(),
    rejectReferral: vi.fn(),
  };
});

import { rejectReferral, resumeReferral } from '../../../src/api/orchestratorClient';

const mockedResume = resumeReferral as unknown as ReturnType<typeof vi.fn>;
const mockedReject = rejectReferral as unknown as ReturnType<typeof vi.fn>;

const ITEM: ReferralQueueItem = {
  riskId: 'risk-1',
  applicantName: 'Alex Rivera',
  referredAt: '2026-10-20T10:00:00Z',
  referralReason: 'High coverage amount',
};

function renderDecision(state: ReferralQueueItem | null) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/underwriter/risk-1', state }]}>
      <Routes>
        <Route path="/underwriter" element={<div>Queue screen</div>} />
        <Route path="/underwriter/:riskId" element={<ReferralDecision />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  mockedResume.mockReset();
  mockedReject.mockReset();
});

describe('ReferralDecision', () => {
  it('shows a warning and a way back when no risk was handed in', () => {
    renderDecision(null);
    expect(screen.getByText(/no longer in the queue/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to queue' })).toBeInTheDocument();
  });

  it('calls resumeReferral with "approve" and returns to the queue on success', async () => {
    mockedResume.mockResolvedValue(undefined);
    renderDecision(ITEM);

    await userEvent.click(screen.getByRole('button', { name: 'Approve' }));

    expect(mockedResume).toHaveBeenCalledWith('risk-1', 'approve');
    expect(await screen.findByText('Queue screen')).toBeInTheDocument();
  });

  it('calls resumeReferral with "approve_with_loading" on that action', async () => {
    mockedResume.mockResolvedValue(undefined);
    renderDecision(ITEM);

    await userEvent.click(screen.getByRole('button', { name: 'Approve with loading' }));

    expect(mockedResume).toHaveBeenCalledWith('risk-1', 'approve_with_loading');
    expect(await screen.findByText('Queue screen')).toBeInTheDocument();
  });

  it('calls rejectReferral on Decline and returns to the queue on success', async () => {
    mockedReject.mockResolvedValue(undefined);
    renderDecision(ITEM);

    await userEvent.click(screen.getByRole('button', { name: 'Decline' }));

    expect(mockedReject).toHaveBeenCalledWith('risk-1');
    expect(await screen.findByText('Queue screen')).toBeInTheDocument();
  });

  it('shows a retryable error and keeps the decision screen on a failed resume', async () => {
    mockedResume.mockRejectedValue(new OrchestratorRequestError('orchestrator unreachable', true));
    renderDecision(ITEM);

    await userEvent.click(screen.getByRole('button', { name: 'Approve' }));

    expect(await screen.findByText(/orchestrator unreachable/)).toBeInTheDocument();
    expect(screen.getByText('Referral decision for risk risk-1')).toBeInTheDocument();
  });

  it('shows a non-retryable error and keeps the decision screen on a failed reject', async () => {
    mockedReject.mockRejectedValue(new OrchestratorRequestError('invalid risk state', false));
    renderDecision(ITEM);

    await userEvent.click(screen.getByRole('button', { name: 'Decline' }));

    expect(await screen.findByText('invalid risk state')).toBeInTheDocument();
    expect(screen.getByText('Referral decision for risk risk-1')).toBeInTheDocument();
  });
});
