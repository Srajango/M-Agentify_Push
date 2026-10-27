import { z } from 'zod';

/**
 * Typed runtime configuration for the orchestrator API client. Build-time values
 * (base URL, timeout) come from Vite's `import.meta.env` so they are baked into the
 * static bundle; `DRY_RUN` is a Node-only test/sandbox toggle read from
 * `process.env` and is never shipped to the browser (it carries no VITE_ prefix).
 */
export interface AppConfig {
  orchestratorBaseUrl: string;
  requestTimeoutMs: number;
  dryRun: boolean;
}

const EnvSchema = z.object({
  VITE_ORCHESTRATOR_BASE_URL: z.string().default(''),
  VITE_ORCHESTRATOR_TIMEOUT_MS: z
    .string()
    .regex(/^\d+$/, 'must be a positive integer number of milliseconds')
    .default('5000'),
  DRY_RUN: z.enum(['true', 'false']).default('false'),
});

function readProcessEnvValue(key: string): string | undefined {
  if (typeof process === 'undefined' || typeof process.env === 'undefined') {
    return undefined;
  }
  return process.env[key];
}

function readRawEnv(): Record<string, string | undefined> {
  const viteEnv = import.meta.env;
  return {
    VITE_ORCHESTRATOR_BASE_URL: viteEnv.VITE_ORCHESTRATOR_BASE_URL ?? readProcessEnvValue('VITE_ORCHESTRATOR_BASE_URL'),
    VITE_ORCHESTRATOR_TIMEOUT_MS: viteEnv.VITE_ORCHESTRATOR_TIMEOUT_MS ?? readProcessEnvValue('VITE_ORCHESTRATOR_TIMEOUT_MS'),
    DRY_RUN: readProcessEnvValue('DRY_RUN'),
  };
}

/**
 * Parses the current environment into a validated AppConfig. Called fresh on every
 * use (never cached at module scope) so per-test `process.env.DRY_RUN` overrides
 * take effect for the test that set them.
 */
export function loadConfig(): AppConfig {
  const parsed = EnvSchema.parse(readRawEnv());
  return {
    orchestratorBaseUrl: parsed.VITE_ORCHESTRATOR_BASE_URL.replace(/\/$/, ''),
    requestTimeoutMs: Number(parsed.VITE_ORCHESTRATOR_TIMEOUT_MS),
    dryRun: parsed.DRY_RUN === 'true',
  };
}
