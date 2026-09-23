import { z } from 'zod'

import { moneyTextSchema } from '@/utils/money-text-schema'

export const categoryLimitSchema = z.object({
  limit: moneyTextSchema,
})

export type CategoryLimitInput = z.infer<typeof categoryLimitSchema>
