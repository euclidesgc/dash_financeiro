import { useId, useRef } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { formatCount } from '@/utils/format-count'
import { formatDate } from '@/utils/format-date'
import { formatDateTime } from '@/utils/format-date-time'
import { formatMoney } from '@/utils/format-money'
import { useApplyProposal } from '@/features/advisor/api/apply-proposal'
import { useDiscardProposal } from '@/features/advisor/api/discard-proposal'
import { useUndoProposal } from '@/features/advisor/api/undo-proposal'
import type { Proposal, ProposalStatus } from '@/features/advisor/types/advisor'

const TRANSACTION_NOUN = { one: 'lançamento', many: 'lançamentos' }
const UNCATEGORISED = 'Sem categoria'
const ACTION_FAILED = 'Não foi possível concluir. Tente de novo.'

const STATUS_BADGES: Record<ProposalStatus, { label: string; classes: string }> = {
  pending: { label: 'Aguardando você', classes: 'bg-amber-100 text-amber-800' },
  applied: { label: 'Aplicada', classes: 'bg-green-100 text-green-800' },
  discarded: { label: 'Descartada', classes: 'bg-gray-100 text-gray-700' },
  undone: { label: 'Desfeita', classes: 'bg-gray-100 text-gray-700' },
}

function actionErrorMessage(error: unknown): string {
  return error instanceof ApiError && error.status !== 422 && error.detail
    ? error.detail
    : ACTION_FAILED
}

function withTime(prefix: string, iso: string | null): string {
  const when = formatDateTime(iso)
  return when ? `${prefix} em ${when}.` : `${prefix}.`
}

function outcome(proposal: Proposal): string {
  if (proposal.status === 'pending') {
    return 'Nada mudou ainda. Confira a lista e aplique.'
  }
  if (proposal.status === 'applied') {
    return withTime('Aplicada', proposal.applied_at)
  }
  if (proposal.status === 'discarded') {
    return withTime('Descartada', proposal.discarded_at) + ' Nada foi alterado.'
  }
  const skipped = proposal.undo_skipped ?? 0
  const kept =
    skipped > 0
      ? ` ${formatCount(skipped, TRANSACTION_NOUN)} que você mudou depois ${skipped === 1 ? 'ficou' : 'ficaram'} como ${skipped === 1 ? 'estava' : 'estavam'}.`
      : ''
  return withTime('Desfeita', proposal.undone_at) + kept
}

function amountClasses(cents: number): string {
  return `tabular-nums font-medium ${cents < 0 ? 'text-red-700' : 'text-gray-900'}`
}

export function ProposalCard({
  conversationId,
  proposal,
}: {
  conversationId: number
  proposal: Proposal
}): React.JSX.Element {
  const titleId = useId()
  const applyProposal = useApplyProposal()
  const discardProposal = useDiscardProposal()
  const undoProposal = useUndoProposal()
  const busy = applyProposal.isPending || discardProposal.isPending || undoProposal.isPending
  const failure = applyProposal.error ?? discardProposal.error ?? undoProposal.error
  const variables = { conversationId, proposalId: proposal.id }
  const badge = STATUS_BADGES[proposal.status]
  // A double click fires both clicks before React disables the button; the
  // ref closes the gate synchronously so only one request leaves.
  const inFlight = useRef(false)

  function run(action: 'apply' | 'discard' | 'undo'): void {
    if (inFlight.current) return
    inFlight.current = true
    applyProposal.reset()
    discardProposal.reset()
    undoProposal.reset()
    const mutation = { apply: applyProposal, discard: discardProposal, undo: undoProposal }[action]
    mutation.mutate(variables, {
      onSettled: () => {
        inFlight.current = false
      },
    })
  }

  return (
    <section
      aria-labelledby={titleId}
      className="mt-2 w-full max-w-[85%] rounded-md border border-gray-200 p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id={titleId} className="min-w-0 font-medium text-gray-900">
          Mudar {formatCount(proposal.items.length, TRANSACTION_NOUN)} para{' '}
          {proposal.target_category}
        </h3>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-sm ${badge.classes}`}>
          {badge.label}
        </span>
      </div>
      <ul
        aria-label="Lançamentos da proposta"
        className="mt-3 max-h-80 divide-y divide-gray-200 overflow-y-auto"
      >
        {proposal.items.map((item) => (
          <li key={item.transaction_id} className="flex items-start justify-between gap-4 py-3">
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-gray-900" title={item.description ?? ''}>
                {item.description ?? 'Sem descrição'}
              </p>
              <p className="text-sm text-gray-600 break-words">
                {item.from_category ?? UNCATEGORISED} → {item.to_category}
              </p>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <span className="text-sm text-gray-600 tabular-nums">{formatDate(item.date)}</span>
              <span className={amountClasses(item.amount_cents)}>
                {formatMoney(item.amount_cents)}
              </span>
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-3 flex justify-between gap-4 border-t border-gray-200 pt-3 text-sm">
        <span className="text-gray-600">Total</span>
        <span className={amountClasses(proposal.total_cents)}>
          {formatMoney(proposal.total_cents)}
        </span>
      </p>
      <p role="status" className="mt-3 text-sm text-gray-600">
        {outcome(proposal)}
      </p>
      {proposal.status === 'pending' ? (
        <div className="mt-3 flex flex-wrap gap-3">
          <Button
            onClick={() => {
              run('apply')
            }}
            disabled={busy}
          >
            {applyProposal.isPending ? 'Aplicando…' : 'Aplicar'}
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              run('discard')
            }}
            disabled={busy}
          >
            {discardProposal.isPending ? 'Descartando…' : 'Descartar'}
          </Button>
        </div>
      ) : null}
      {proposal.status === 'applied' ? (
        <div className="mt-3">
          <Button
            variant="secondary"
            onClick={() => {
              run('undo')
            }}
            disabled={busy}
          >
            {undoProposal.isPending ? 'Desfazendo…' : 'Desfazer'}
          </Button>
        </div>
      ) : null}
      {failure ? <Alert message={actionErrorMessage(failure)} /> : null}
    </section>
  )
}
