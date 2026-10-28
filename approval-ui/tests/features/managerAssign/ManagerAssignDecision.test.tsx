import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ManagerAssignDecision from '../../../src/features/managerAssign/ManagerAssignDecision';
import { OrchestratorRequestError, type ManagerAssignQueueItem } from '../../../src/api/orchestratorClient';

vi.mock('../../../src/api/orchestratorClient', async () => {
  const actual = await vi.importActual<typeof import('../../../src/api/orchestratorClient')>(
    '../../../src/api/orchestratorClient',
  );
  return {
    ...actual,
    resumeManagerAssign: vi.fn(),
  };
});

import { resumeManagerAssign } from '../../../src/api/orchestratorClient';

const mockedResume = resumeManagerAssign as unknown as ReturnType<typeof vi.fn>;

const ITEM: ManagerAssignQueueItem = {
  leadId: 'lead-1',
  city: 'Reno',
  requestedAt: '2026-10-20T10:00:00Z',
  candidateAgents: [
    { agentId: 'agent-1', name: 'Jordan Blake' },
    { agentId: 'agent-2', name: 'Casey Nguyen' },
  ],
};

function renderDecision(state: ManagerAssignQueueItem | null) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/manager/lead-1', state }]}>
      <Routes>
        <Route path="/manager" element={<div>Queue screen</div>} />
        <Route path="/manager/:leadId" element={<ManagerAssignDecision />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  mockedResume.mockReset();
});

describe('ManagerAssignDecision', () => {
  it('shows a warning and a way back when no lead was handed in', () => {
    renderDecision(null);
    expect(screen.getByText(/no longer in the queue/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to queue' })).toBeInTheDocument();
  });

  it('calls resumeManagerAssign with the chosen agent and returns to the queue on success', async () => {
    mockedResume.mockResolvedValue(undefined);
    renderDecision(ITEM);

    await userEvent.click(screen.getByLabelText('Active agent'));
    await userEvent.click(await screen.findByRole('option', { name: 'Casey Nguyen' }));
    await userEvent.click(screen.getByRole('button', { name: 'Confirm assignment' }));

    expect(mockedResume).toHaveBeenCalledWith('lead-1', 'agent-2');
    expect(await screen.findByText('Queue screen')).toBeInTheDocument();
  });

  it('shows a retryable error and keeps the decision screen on a failed resume', async () => {
    mockedResume.mockRejectedValue(new OrchestratorRequestError('orchestrator unreachable', true));
    renderDecision(ITEM);

    await userEvent.click(screen.getByLabelText('Active agent'));
    await userEvent.click(await screen.findByRole('option', { name: 'Jordan Blake' }));
    await userEvent.click(screen.getByRole('button', { name: 'Confirm assignment' }));

    expect(await screen.findByText(/orchestrator unreachable/)).toBeInTheDocument();
    expect(screen.getByText('Assign agent for lead lead-1')).toBeInTheDocument();
  });
});
