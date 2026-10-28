import { z } from 'zod';
import { loadConfig, type AppConfig } from './config';

/**
 * Thrown when a call to the orchestrator fails. `retryable` distinguishes a
 * transient failure (network error, timeout, 5xx) from a request the orchestrator
 * rejected outright (4xx), so callers can decide whether to offer a retry.
 */
export class OrchestratorRequestError extends Error {
  readonly retryable: boolean;

  constructor(message: string, retryable: boolean) {
    super(message);
    this.name = 'OrchestratorRequestError';
    this.retryable = retryable;
  }
}

function toMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

const HealthResponseSchema = z.object({}).passthrough();
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

const ActiveAgentOptionSchema = z.object({
  agentId: z.string(),
  name: z.string(),
});
export type ActiveAgentOption = z.infer<typeof ActiveAgentOptionSchema>;

const ManagerAssignQueueItemSchema = z.object({
  leadId: z.string(),
  city: z.string(),
  requestedAt: z.string(),
  candidateAgents: z.array(ActiveAgentOptionSchema),
});
export type ManagerAssignQueueItem = z.infer<typeof ManagerAssignQueueItemSchema>;

const ManagerAssignQueueResponseSchema = z.array(ManagerAssignQueueItemSchema);

const ReferralQueueItemSchema = z.object({
  riskId: z.string(),
  applicantName: z.string(),
  referredAt: z.string(),
  referralReason: z.string(),
});
export type ReferralQueueItem = z.infer<typeof ReferralQueueItemSchema>;

const ReferralQueueResponseSchema = z.array(ReferralQueueItemSchema);

export type ReferralDecisionKind = 'approve' | 'approve_with_loading';

/**
 * The op_id of each operation in the FROZEN contract's `consumed` block. Sent as
 * a literal field on every request for that operation so the call is unambiguously
 * tied to the op_id the contract declared, independent of the path chosen for it.
 */
const MANAGER_ASSIGN_RESUME_OP_ID = 'op_ce482f80d0fcea34';
const REFERRAL_RESUME_OP_ID = 'op_e24ddacd8a90f3a1';
const REFERRAL_REJECT_OP_ID = 'op_bc42e7eadaa65523';

async function withTimeout<T>(config: AppConfig, path: string, perform: (signal: AbortSignal) => Promise<T>): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), config.requestTimeoutMs);
  try {
    return await perform(controller.signal);
  } catch (error) {
    throw new OrchestratorRequestError(
      `Request to ${path} did not reach the orchestrator: ${toMessage(error)}`,
      true,
    );
  } finally {
    clearTimeout(timer);
  }
}

function ensureOk(res: Response, path: string): void {
  if (!res.ok) {
    throw new OrchestratorRequestError(`Orchestrator responded ${res.status} for ${path}`, res.status >= 500);
  }
}

async function requestJson<T>(
  config: AppConfig,
  path: string,
  perform: (signal: AbortSignal) => Promise<Response>,
  schema: z.ZodType<T>,
  dryRunFixture: T,
): Promise<T> {
  if (config.dryRun) {
    return dryRunFixture;
  }
  const res = await withTimeout(config, path, perform);
  ensureOk(res, path);
  const body: unknown = await res.json();
  return schema.parse(body);
}

async function requestVoid(
  config: AppConfig,
  path: string,
  perform: (signal: AbortSignal) => Promise<Response>,
): Promise<void> {
  if (config.dryRun) {
    return;
  }
  const res = await withTimeout(config, path, perform);
  ensureOk(res, path);
}

function jsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json' };
}

/** Calls the orchestrator's health endpoint, `GET /health`. */
export async function fetchHealth(): Promise<HealthResponse> {
  const config = loadConfig();
  return requestJson(
    config,
    '/health',
    (signal) => fetch(`${config.orchestratorBaseUrl}/health`, { method: 'GET', signal }),
    HealthResponseSchema,
    {},
  );
}

/**
 * Lists the leads paused at the `manager_manual_assign` human gate, each carrying
 * the active agents the manager may assign in place of the uncovered one.
 */
export async function fetchManagerAssignQueue(): Promise<ManagerAssignQueueItem[]> {
  const config = loadConfig();
  return requestJson(
    config,
    '/human-gates/manager_manual_assign/queue',
    (signal) =>
      fetch(`${config.orchestratorBaseUrl}/human-gates/manager_manual_assign/queue`, { method: 'GET', signal }),
    ManagerAssignQueueResponseSchema,
    [],
  );
}

/**
 * Resumes the `manager_manual_assign` gate for one lead with the agent the manager
 * picked. This is op_ce482f80d0fcea34 from the FROZEN contract's `consumed`
 * block — MANAGER_ASSIGN_RESUME_OP_ID is sent as a literal field on the request
 * so the call is traceable to that exact op_id.
 */
export async function resumeManagerAssign(leadId: string, assignedAgentId: string): Promise<void> {
  const config = loadConfig();
  await requestVoid(
    config,
    '/human-gates/manager_manual_assign/resume',
    (signal) =>
      fetch(`${config.orchestratorBaseUrl}/human-gates/manager_manual_assign/resume`, {
        method: 'POST',
        headers: jsonHeaders(),
        body: JSON.stringify({ opId: MANAGER_ASSIGN_RESUME_OP_ID, leadId, assignedAgentId }),
        signal,
      }),
  );
}

/**
 * Lists the risks paused at the `underwriter_review_referral` human gate, awaiting
 * an underwriter's approve/decline decision.
 */
export async function fetchReferralQueue(): Promise<ReferralQueueItem[]> {
  const config = loadConfig();
  return requestJson(
    config,
    '/human-gates/underwriter_review_referral/queue',
    (signal) =>
      fetch(`${config.orchestratorBaseUrl}/human-gates/underwriter_review_referral/queue`, {
        method: 'GET',
        signal,
      }),
    ReferralQueueResponseSchema,
    [],
  );
}

/**
 * Resumes the `underwriter_review_referral` gate for one risk with the
 * underwriter's approve decision, "approve" or "approve_with_loading". This is
 * op_e24ddacd8a90f3a1 from the FROZEN contract's `consumed` block —
 * REFERRAL_RESUME_OP_ID is sent as a literal field on the request so the call
 * is traceable to that exact op_id.
 */
export async function resumeReferral(riskId: string, decision: ReferralDecisionKind): Promise<void> {
  const config = loadConfig();
  await requestVoid(
    config,
    '/human-gates/underwriter_review_referral/resume',
    (signal) =>
      fetch(`${config.orchestratorBaseUrl}/human-gates/underwriter_review_referral/resume`, {
        method: 'POST',
        headers: jsonHeaders(),
        body: JSON.stringify({ opId: REFERRAL_RESUME_OP_ID, riskId, decision }),
        signal,
      }),
  );
}

/**
 * Rejects the `underwriter_review_referral` gate for one risk, recording the
 * underwriter's decline. This is op_bc42e7eadaa65523 from the FROZEN contract's
 * `consumed` block — REFERRAL_REJECT_OP_ID is sent as a literal field on the
 * request so the call is traceable to that exact op_id.
 */
export async function rejectReferral(riskId: string, reason?: string): Promise<void> {
  const config = loadConfig();
  await requestVoid(
    config,
    '/human-gates/underwriter_review_referral/reject',
    (signal) =>
      fetch(`${config.orchestratorBaseUrl}/human-gates/underwriter_review_referral/reject`, {
        method: 'POST',
        headers: jsonHeaders(),
        body: JSON.stringify({ opId: REFERRAL_REJECT_OP_ID, riskId, reason }),
        signal,
      }),
  );
}

export { toMessage };
