import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import {
  OrchestratorRequestError,
  fetchHealth,
  fetchManagerAssignQueue,
  fetchReferralQueue,
  rejectReferral,
  resumeManagerAssign,
  resumeReferral,
} from '../../src/api/orchestratorClient';

const BASE_URL = 'http://localhost:5096';

const server = setupServer();

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  delete process.env.DRY_RUN;
});
afterAll(() => server.close());

describe('orchestratorClient (DRY_RUN=true, no network)', () => {
  it('fetchHealth returns the dry-run fixture without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(fetchHealth()).resolves.toEqual({});
  });

  it('fetchManagerAssignQueue returns an empty fixture list without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(fetchManagerAssignQueue()).resolves.toEqual([]);
  });

  it('resumeManagerAssign resolves without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(resumeManagerAssign('lead-1', 'agent-1')).resolves.toBeUndefined();
  });

  it('fetchReferralQueue returns an empty fixture list without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(fetchReferralQueue()).resolves.toEqual([]);
  });

  it('resumeReferral resolves without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(resumeReferral('risk-1', 'approve')).resolves.toBeUndefined();
  });

  it('rejectReferral resolves without any network call', async () => {
    process.env.DRY_RUN = 'true';
    await expect(rejectReferral('risk-1', 'too risky')).resolves.toBeUndefined();
  });
});

describe('orchestratorClient (DRY_RUN=false, stubbed transport)', () => {
  it('GET /health sends the real request and parses the frozen response_example ({})', async () => {
    process.env.DRY_RUN = 'false';
    let seenMethod = '';
    let seenUrl = '';
    server.use(
      http.get(`${BASE_URL}/health`, ({ request }) => {
        seenMethod = request.method;
        seenUrl = request.url;
        return HttpResponse.json({});
      }),
    );

    const result = await fetchHealth();

    expect(seenMethod).toBe('GET');
    expect(seenUrl).toBe(`${BASE_URL}/health`);
    expect(result).toEqual({});
  });

  it('fetchManagerAssignQueue sends GET /human-gates/manager_manual_assign/queue and parses the list', async () => {
    process.env.DRY_RUN = 'false';
    server.use(
      http.get(`${BASE_URL}/human-gates/manager_manual_assign/queue`, () =>
        HttpResponse.json([
          {
            leadId: 'lead-1',
            city: 'Reno',
            requestedAt: '2026-10-20T10:00:00Z',
            candidateAgents: [{ agentId: 'agent-1', name: 'Jordan Blake' }],
          },
        ]),
      ),
    );

    const items = await fetchManagerAssignQueue();
    expect(items).toHaveLength(1);
    expect(items[0].leadId).toBe('lead-1');
  });

  it('resumeManagerAssign sends POST /human-gates/manager_manual_assign/resume with the chosen agent', async () => {
    process.env.DRY_RUN = 'false';
    let seenMethod = '';
    let seenUrl = '';
    let seenBody: unknown;
    let seenContentType: string | null = null;
    server.use(
      http.post(`${BASE_URL}/human-gates/manager_manual_assign/resume`, async ({ request }) => {
        seenMethod = request.method;
        seenUrl = request.url;
        seenContentType = request.headers.get('content-type');
        seenBody = await request.json();
        return new HttpResponse(null, { status: 200 });
      }),
    );

    await resumeManagerAssign('lead-1', 'agent-2');

    expect(seenMethod).toBe('POST');
    expect(seenUrl).toBe(`${BASE_URL}/human-gates/manager_manual_assign/resume`);
    expect(seenContentType).toBe('application/json');
    expect(seenBody).toEqual({ opId: 'op_ce482f80d0fcea34', leadId: 'lead-1', assignedAgentId: 'agent-2' });
  });

  it('resumeManagerAssign throws a non-retryable OrchestratorRequestError on a 4xx response', async () => {
    process.env.DRY_RUN = 'false';
    server.use(
      http.post(`${BASE_URL}/human-gates/manager_manual_assign/resume`, () =>
        HttpResponse.json({ error: 'agent not active' }, { status: 400 }),
      ),
    );

    await expect(resumeManagerAssign('lead-1', 'agent-2')).rejects.toSatisfy((error: unknown) => {
      return error instanceof OrchestratorRequestError && error.retryable === false;
    });
  });

  it('resumeReferral sends POST /human-gates/underwriter_review_referral/resume with the decision', async () => {
    process.env.DRY_RUN = 'false';
    let seenBody: unknown;
    server.use(
      http.post(`${BASE_URL}/human-gates/underwriter_review_referral/resume`, async ({ request }) => {
        seenBody = await request.json();
        return new HttpResponse(null, { status: 200 });
      }),
    );

    await resumeReferral('risk-1', 'approve_with_loading');
    expect(seenBody).toEqual({ opId: 'op_e24ddacd8a90f3a1', riskId: 'risk-1', decision: 'approve_with_loading' });
  });

  it('resumeReferral throws a retryable OrchestratorRequestError on a 5xx response', async () => {
    process.env.DRY_RUN = 'false';
    server.use(
      http.post(`${BASE_URL}/human-gates/underwriter_review_referral/resume`, () =>
        HttpResponse.json({ error: 'unavailable' }, { status: 503 }),
      ),
    );

    await expect(resumeReferral('risk-1', 'approve')).rejects.toSatisfy((error: unknown) => {
      return error instanceof OrchestratorRequestError && error.retryable === true;
    });
  });

  it('rejectReferral sends POST /human-gates/underwriter_review_referral/reject with the reason', async () => {
    process.env.DRY_RUN = 'false';
    let seenBody: unknown;
    server.use(
      http.post(`${BASE_URL}/human-gates/underwriter_review_referral/reject`, async ({ request }) => {
        seenBody = await request.json();
        return new HttpResponse(null, { status: 200 });
      }),
    );

    await rejectReferral('risk-1', 'too risky');
    expect(seenBody).toEqual({ opId: 'op_bc42e7eadaa65523', riskId: 'risk-1', reason: 'too risky' });
  });

  it('rejectReferral throws a retryable OrchestratorRequestError on a network failure', async () => {
    process.env.DRY_RUN = 'false';
    server.use(
      http.post(`${BASE_URL}/human-gates/underwriter_review_referral/reject`, () => HttpResponse.error()),
    );

    await expect(rejectReferral('risk-1')).rejects.toSatisfy((error: unknown) => {
      return error instanceof OrchestratorRequestError && error.retryable === true;
    });
  });
});
