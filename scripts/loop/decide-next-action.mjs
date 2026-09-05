#!/usr/bin/env node
/* The loop's decision: what the next session does, read from the state.

   ## Why the decision does not live in the shell

   A shell script is the only layer here without lint, types or tests. An
   autonomous engine that decides wrong in silence is the expensive version of
   a gate that exits 0 because it could not measure — it decides wrong all
   night. So the decision is a pure function over the state, exported and
   tested against the real state machine; the `.sh` only calls it and obeys.

   ## What it never decides

   Merging. It opens a stacked PR and stops. Merge is irreversible for someone
   who is asleep, and the stack exists precisely so the merge is a decision the
   developer takes later, awake, all at once.

   ## Usage

   `node scripts/loop/decide-next-action.mjs [--root <dir>]`
   Prints JSON on stdout. Exit code: `0` there is an action, `1` stop. */

import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');

const STAGE_ORDER = ['discovery', 'brief', 'prd', 'spec', 'plan', 'execute', 'done'];

const stop = (reason, extra = {}) => ({ action: 'stop', reason, ...extra });

export const countPhases = (root, item) => {
  const file = join(root, 'product', 'items', item, '03-plan.md');
  if (!existsSync(file)) return 0;
  return [...readFileSync(file, 'utf8').matchAll(/^## +Fase +(\d+)\b/gm)].length;
};

export const readRoadmapQueue = (root) => {
  const file = join(root, 'product', 'roadmap.md');
  if (!existsSync(file)) return [];
  const body = readFileSync(file, 'utf8');
  return [...body.matchAll(/^\s*- \[( |-|x)\] `(\d{3}-[a-z0-9-]+)`/gm)].map((m) => ({
    id: m[2],
    done: m[1] === 'x',
    started: m[1] === '-',
  }));
};

/* No file is a fresh project (nothing pulled yet); an unreadable file is a
   reason to stop — deciding over a state you could not read is deciding
   blind. */
export const readState = (root) => {
  const file = join(root, 'product', 'state.json');
  if (!existsSync(file)) return { schema: 1, active_item: null, items: {} };
  try {
    return JSON.parse(readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
};

/* `state` is product/state.json as written by state.py; `phasesOf(item)` is the
   number of phases declared in that item's plan. Both are injected so the
   decision can be tested without a repository. */
export const decide = (state, { phasesOf, queue }) => {
  if (state === null || state === undefined) {
    return stop('could not read product/state.json');
  }

  const items = state.items ?? {};
  const id = state.active_item;

  if (!id || !items[id] || items[id].stage === 'done') {
    const pending = queue.filter((entry) => !entry.done && items[entry.id]?.stage !== 'done');
    const next = pending[0];
    if (!next) return stop('every roadmap item is done — nothing left to pull');
    if (items[next.id]) return { action: 'activate', item: next.id, stage: items[next.id].stage };
    return { action: 'create', item: next.id, stage: 'discovery' };
  }

  const item = items[id];
  const phases = item.phases ?? {};

  const escalated = Object.entries(phases).find(([, p]) => p?.status === 'escalada_humana');
  if (escalated) {
    return stop(
      `phase ${escalated[0]} of ${id} is escalated to a human — two rejections in a row mean the cause is upstream`,
    );
  }

  if (item.criteria_exception) {
    return {
      action: 'repair-criteria',
      item: id,
      file: item.criteria_exception.file,
      agent: item.criteria_exception.agent,
    };
  }

  const contract = Object.entries(item.divergences ?? {}).find(
    ([, d]) => d.kind === 'contrato' && d.status === 'PENDENTE',
  );
  if (contract) {
    return stop(
      `contract divergence ${contract[0]} is unratified — a wrong contract premise spreads to every consumer, so a human decides it`,
    );
  }

  const stage = item.stage;
  if (!STAGE_ORDER.includes(stage)) return stop(`unknown stage: ${stage}`);
  const plan = join('product', 'items', id, '03-plan.md');

  /* The plan approved is the gate; `execute` is entered by the first
     `phase-start`. An approved plan with no phase started is phase 1. */
  const planApproved = Boolean(item.approvals?.plan?.at);
  if (stage !== 'execute' && !(stage === 'plan' && planApproved)) {
    return { action: 'stage', item: id, stage };
  }

  const total = phasesOf(id);
  const current = item.current_phase;

  if (current === null || current === undefined) {
    return { action: 'phase', item: id, phase: 1, plan };
  }

  const entry = phases[String(current)] ?? {};
  switch (entry.status) {
    case 'bloqueada':
      return stop(`phase ${current} of ${id} is blocked on a contract divergence`);
    case 'criterio_invalido':
      return { action: 'repair-criteria', item: id, file: plan, agent: 'plan-writer' };
    case 'aprovada': {
      /* An approved current phase is the previous task, not the next one.
         Without this step the engine reopens the phase it just closed and the
         night goes in circles — which is how the first dry run caught it. */
      const next = Number(current) + 1;
      if (total > 0 && next > total) {
        return { action: 'close', item: id, reason: `all ${total} phases are approved` };
      }
      return { action: 'phase', item: id, phase: next, plan };
    }
    case 'reprovada':
      return { action: 'phase', item: id, phase: Number(current), plan, retry: true };
    default:
      return { action: 'phase', item: id, phase: Number(current), plan };
  }
};

const isMain = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (isMain) {
  const flag = process.argv.indexOf('--root');
  const root = flag === -1 ? ROOT : resolve(process.argv[flag + 1]);
  const decision = decide(readState(root), {
    phasesOf: (item) => countPhases(root, item),
    queue: readRoadmapQueue(root),
  });
  decision.prompt = join('product', 'prompt-da-proxima-sessao.md');
  process.stdout.write(`${JSON.stringify(decision, null, 2)}\n`);
  process.exit(decision.action === 'stop' ? 1 : 0);
}
