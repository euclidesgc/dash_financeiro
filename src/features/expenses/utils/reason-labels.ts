import type { NotExpenseReason } from '@/features/expenses/types/expense'

export const REASON_OPTIONS: { value: NotExpenseReason; label: string }[] = [
  { value: 'own_transfer', label: 'Transferência entre minhas contas' },
  { value: 'refund', label: 'Estorno' },
  { value: 'other', label: 'Outro' },
]

export const REASON_LABELS: Record<NotExpenseReason, string> = {
  own_transfer: 'Transferência entre minhas contas',
  refund: 'Estorno',
  other: 'Outro',
}
