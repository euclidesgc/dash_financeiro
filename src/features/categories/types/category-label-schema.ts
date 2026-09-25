import { z } from 'zod'

export const categoryLabelSchema = z.object({
  label: z.string().trim().min(1, 'Informe o nome da categoria.'),
})

export type CategoryLabelInput = z.infer<typeof categoryLabelSchema>
