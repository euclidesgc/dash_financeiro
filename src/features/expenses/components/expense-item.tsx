import { formatDate } from '@/utils/format-date'
import { formatMoney } from '@/utils/format-money'
import { CategoryPicker } from '@/features/expenses/components/category-picker'
import type { Category, Expense } from '@/features/expenses/types/expense'

function accountLabel(expense: Expense): string {
  const parts = [expense.account_name, expense.account_institution].filter(
    (part): part is string => part !== null,
  )
  return parts.length > 0 ? parts.join(' · ') : 'Conta desconhecida'
}

export function ExpenseItem({
  expense,
  categories,
  categoriesReady,
}: {
  expense: Expense
  categories: Category[]
  categoriesReady: boolean
}): React.JSX.Element {
  const amountColor = expense.amount_cents < 0 ? 'text-red-700' : 'text-gray-900'

  return (
    <li className="flex items-start justify-between gap-4 py-3">
      <div className="min-w-0 flex-1">
        <p className="font-medium truncate text-gray-900">
          {expense.description ?? 'Sem descrição'}
        </p>
        {expense.payee_name !== null ? (
          <p className="text-sm text-gray-600 truncate">{expense.payee_name}</p>
        ) : null}
        <p className="text-sm text-gray-600 truncate">{accountLabel(expense)}</p>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1">
        <span className="text-sm text-gray-600 tabular-nums">{formatDate(expense.date)}</span>
        <CategoryPicker expense={expense} categories={categories} categoriesReady={categoriesReady} />
        <span className={`tabular-nums font-medium ${amountColor}`}>
          {formatMoney(expense.amount_cents)}
        </span>
      </div>
    </li>
  )
}
