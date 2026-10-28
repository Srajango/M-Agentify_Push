import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../../src/api/orchestratorClient', async () => {
  const actual = await vi.importActual<typeof import('../../src/api/orchestratorClient')>(
    '../../src/api/orchestratorClient',
  );
  return {
    ...actual,
    fetchHealth: vi.fn().mockResolvedValue({}),
    fetchManagerAssignQueue: vi.fn().mockResolvedValue([]),
    fetchReferralQueue: vi.fn().mockResolvedValue([]),
  };
});

import App from '../../src/app/App';
import { fetchHealth } from '../../src/api/orchestratorClient';

const mockedFetchHealth = fetchHealth as unknown as ReturnType<typeof vi.fn>;

afterEach(() => {
  vi.clearAllMocks();
});

describe('App', () => {
  it('imports and renders without throwing, showing both area tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('tab', { name: 'Manager' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Underwriter' })).toBeInTheDocument();
    expect(await screen.findByText('No leads are waiting for manual assignment.')).toBeInTheDocument();
    expect(screen.queryByText(/orchestrator could not be reached/)).not.toBeInTheDocument();
  });

  it('shows a warning banner when the orchestrator health check fails', async () => {
    mockedFetchHealth.mockRejectedValue(new Error('connect ECONNREFUSED'));

    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/orchestrator could not be reached/)).toBeInTheDocument();
  });
});
