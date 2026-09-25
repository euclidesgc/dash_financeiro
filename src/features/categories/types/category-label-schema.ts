import { z } from 'zod'

export const CATEGORY_LABEL_MAX = 40

export const CATEGORY_LABEL_TOO_LONG = `O nome da categoria pode ter no máximo ${String(CATEGORY_LABEL_MAX)} caracteres.`

export const categoryLabelSchema = z.object({
  label: z
    .string()
    .trim()
    .min(1, 'Informe o nome da categoria.')
    .max(CATEGORY_LABEL_MAX, CATEGORY_LABEL_TOO_LONG),
})

export type CategoryLabelInput = z.infer<typeof categoryLabelSchema>
