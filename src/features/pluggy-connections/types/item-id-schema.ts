import { z } from 'zod'

export const ITEM_ID_MESSAGE = 'Informe um identificador de conexão da Pluggy (formato 8-4-4-4-12).'

const ITEM_ID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export const itemIdSchema = z.object({
  itemId: z.string().trim().regex(ITEM_ID_PATTERN, ITEM_ID_MESSAGE),
})

export type ItemIdInput = z.infer<typeof itemIdSchema>
