import { z } from 'zod'

export const QUESTION_MAX = 500

export const questionSchema = z.object({
  text: z
    .string()
    .trim()
    .min(1, 'Escreva a pergunta.')
    .max(QUESTION_MAX, `A pergunta passa de ${String(QUESTION_MAX)} caracteres.`),
})

export type QuestionInput = z.infer<typeof questionSchema>
