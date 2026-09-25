import { expect, test } from 'vitest'

import { categoryLabelSchema } from '@/features/categories/types/category-label-schema'

test('a name one over the ceiling is refused with the server message', () => {
  const result = categoryLabelSchema.safeParse({ label: 'a'.repeat(41) })

  expect(result.success).toBe(false)
  expect(result.error?.issues[0]?.message).toBe(
    'O nome da categoria pode ter no máximo 40 caracteres.',
  )
})

test('a name at the ceiling is accepted, measured without the spaces around it', () => {
  const result = categoryLabelSchema.safeParse({ label: `  ${'a'.repeat(40)}  ` })

  expect(result.success).toBe(true)
  expect(result.data?.label).toBe('a'.repeat(40))
})
