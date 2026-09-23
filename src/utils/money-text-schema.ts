import { z } from 'zod'

export const moneyTextSchema = z
  .string()
  .trim()
  .refine(
    (value) => value === '' || /^\d+([.,]\d{1,2})?$/.test(value),
    'Use no máximo duas casas decimais.',
  )
  .refine(
    (value) => value === '' || Number(value.replace(',', '.')) > 0,
    'Informe um valor maior que zero.',
  )
