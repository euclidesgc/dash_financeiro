import type { CategorySignal } from '@/features/expenses/types/expense'

export const SIGNAL_LABELS: Record<CategorySignal, { text: string; className: string }> = {
  within: { text: 'Dentro', className: 'bg-green-100 text-green-800' },
  warning: { text: 'Atenção', className: 'bg-amber-100 text-amber-800' },
  over: { text: 'Acima', className: 'bg-red-100 text-red-800' },
}
