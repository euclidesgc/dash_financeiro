import { z } from 'zod'

import { moneyTextSchema } from '@/utils/money-text-schema'

export const ceilingSchema = z.object({
  ceiling: moneyTextSchema,
})

export type CeilingInput = z.infer<typeof ceilingSchema>
