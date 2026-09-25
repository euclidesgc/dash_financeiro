import { z } from 'zod'

import { parseMoneyText } from '@/utils/money-text'
import type { MoneyTextRejection } from '@/utils/money-text'

const REJECTION_MESSAGES: Record<MoneyTextRejection, string> = {
  empty: 'Informe um valor.',
  format: 'Use o formato 1.500,00.',
  decimals: 'Use no máximo duas casas decimais.',
  'not-positive': 'Informe um valor maior que zero.',
}

export const moneyTextSchema = z.string().superRefine((value, context) => {
  const result = parseMoneyText(value)
  if (!result.ok) {
    context.addIssue({ code: z.ZodIssueCode.custom, message: REJECTION_MESSAGES[result.reason] })
  }
})
