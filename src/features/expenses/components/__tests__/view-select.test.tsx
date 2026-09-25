import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'

import { renderWithProviders } from '@/testing/test-utils'

import { ViewSelect } from '../view-select'

test('shows the label "Mostrar" with the options in order', () => {
  renderWithProviders(<ViewSelect value="expenses" onChange={vi.fn()} />)

  const combobox = screen.getByLabelText('Mostrar')
  expect(combobox.tagName).toBe('SELECT')
  const options = within(combobox).getAllByRole('option')
  expect(options.map((option) => option.textContent)).toEqual(['Gastos', 'Não são gastos', 'Entradas'])
  expect(options.map((option) => (option as HTMLOptionElement).value)).toEqual([
    'expenses',
    'excluded',
    'income',
  ])
  expect(combobox).toHaveValue('expenses')
})

test('calls onChange with the chosen view', async () => {
  const onChange = vi.fn()
  renderWithProviders(<ViewSelect value="expenses" onChange={onChange} />)

  await userEvent.selectOptions(screen.getByLabelText('Mostrar'), 'excluded')

  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenCalledWith('excluded')
})

test('calls onChange with "income"', async () => {
  const onChange = vi.fn()
  renderWithProviders(<ViewSelect value="expenses" onChange={onChange} />)

  await userEvent.selectOptions(screen.getByLabelText('Mostrar'), 'income')

  expect(onChange).toHaveBeenCalledTimes(1)
  expect(onChange).toHaveBeenCalledWith('income')
})
