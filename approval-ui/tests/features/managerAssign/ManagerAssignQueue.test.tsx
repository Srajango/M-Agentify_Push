import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ManagerAssignQueue from '../../../src/features/managerAssign/ManagerAssignQueue';
import { OrchestratorRequestError } from '../../../src/api/orchestratorClient';

vi.mock('../../../src/api/orchestratorClient', async () => {
  const actual = await vi.importActual<typeof import('../../../src/api/orchestratorClient')>(
    '../../../src/api/orchestratorClient',
  );
  return {
    ...actual,
    fetchManagerAssignQueue: vi.fn(),
  };
});

import { fetchManagerAssignQueue } from '../../../src/api/orchestratorClient';

const mockedFetch = fetchManagerAssignQueue as unknown as ReturnType<typeof vi.fn>;

function renderQueue() {
  return render(
    <MemoryRouter initialEntries={['/manager']}>
      <Routes>
        <Route path="/manager" element={<ManagerAssignQueue />} />
        <Route path="/manager/:leadId" element={<div>Decision screen</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  mockedFetch.mockReset();
});

describe('ManagerAssignQueue', () => {
  it('shows the loading state before the fetch resolves', async () => {
    let resolveFetch: (value: unknown[]) => void = () => {};
    mockedFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
    );

    renderQueue();

    expect(screen.getByLabelText('Loading leads waiting for manual assignment')).toBeInTheDocument();
    resolveFetch([]);
    await waitFor(() => expect(screen.queryByLabelText(/Loading/)).not.toBeInTheDocument());
  });

  it('shows the empty state when no leads are queued', async () => {
    mockedFetch.mockResolvedValue([]);
    renderQueue();
    expect(await screen.findByText('No leads are waiting for manual assignment.')).toBeInTheDocument();
  });

  it('shows a retryable error and retries on click', async () => {
    mockedFetch
      .mockRejectedValueOnce(new OrchestratorRequestError('orchestrator unreachable', true))
      .mockResolvedValueOnce([]);

    renderQueue();

    expect(await screen.findByText('orchestrator unreachable')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('No leads are waiting for manual assignment.')).toBeInTheDocument();
    expect(mockedFetch).toHaveBeenCalledTimes(2);
  });

  it('lists queued leads and navigates to the decision screen on selection', async () => {
    mockedFetch.mockResolvedValue([
      {
        leadId: 'lead-1',
        city: 'Reno',
        requestedAt: '2026-10-20T10:00:00Z',
        candidateAgents: [{ agentId: 'agent-1', name: 'Jordan Blake' }],
      },
    ]);

    renderQueue();

    const row = await screen.findByText('Lead lead-1 — Reno');
    await userEvent.click(row);
    expect(await screen.findByText('Decision screen')).toBeInTheDocument();
  });
});
