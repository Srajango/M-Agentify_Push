import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ReferralQueue from '../../../src/features/underwriterReferral/ReferralQueue';
import { OrchestratorRequestError } from '../../../src/api/orchestratorClient';

vi.mock('../../../src/api/orchestratorClient', async () => {
  const actual = await vi.importActual<typeof import('../../../src/api/orchestratorClient')>(
    '../../../src/api/orchestratorClient',
  );
  return {
    ...actual,
    fetchReferralQueue: vi.fn(),
  };
});

import { fetchReferralQueue } from '../../../src/api/orchestratorClient';

const mockedFetch = fetchReferralQueue as unknown as ReturnType<typeof vi.fn>;

function renderQueue() {
  return render(
    <MemoryRouter initialEntries={['/underwriter']}>
      <Routes>
        <Route path="/underwriter" element={<ReferralQueue />} />
        <Route path="/underwriter/:riskId" element={<div>Decision screen</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  mockedFetch.mockReset();
});

describe('ReferralQueue', () => {
  it('shows the loading state before the fetch resolves', async () => {
    let resolveFetch: (value: unknown[]) => void = () => {};
    mockedFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
    );

    renderQueue();

    expect(screen.getByLabelText('Loading risks waiting for a referral decision')).toBeInTheDocument();
    resolveFetch([]);
    await waitFor(() => expect(screen.queryByLabelText(/Loading/)).not.toBeInTheDocument());
  });

  it('shows the empty state when no risks are queued', async () => {
    mockedFetch.mockResolvedValue([]);
    renderQueue();
    expect(await screen.findByText('No risks are waiting for a referral decision.')).toBeInTheDocument();
  });

  it('shows a retryable error and retries on click', async () => {
    mockedFetch
      .mockRejectedValueOnce(new OrchestratorRequestError('orchestrator unreachable', true))
      .mockResolvedValueOnce([]);

    renderQueue();

    expect(await screen.findByText('orchestrator unreachable')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('No risks are waiting for a referral decision.')).toBeInTheDocument();
    expect(mockedFetch).toHaveBeenCalledTimes(2);
  });

  it('lists queued risks and navigates to the decision screen on selection', async () => {
    mockedFetch.mockResolvedValue([
      {
        riskId: 'risk-1',
        applicantName: 'Alex Rivera',
        referredAt: '2026-10-20T10:00:00Z',
        referralReason: 'High coverage amount',
      },
    ]);

    renderQueue();

    const row = await screen.findByText('Risk risk-1 — Alex Rivera');
    await userEvent.click(row);
    expect(await screen.findByText('Decision screen')).toBeInTheDocument();
  });
});
