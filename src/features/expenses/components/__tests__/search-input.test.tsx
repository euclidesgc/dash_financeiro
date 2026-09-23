import { afterEach, expect, test, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { fireEvent, render, screen } from '@testing-library/react'

import { SearchInput } from '@/features/expenses/components/search-input'

afterEach(() => {
  vi.useRealTimers()
})

test('renders the label, the placeholder and no clear button when empty', () => {
  render(<SearchInput value={null} onCommit={vi.fn()} />)

  const input = screen.getByLabelText('Buscar')
  expect(input).toHaveAttribute('type', 'search')
  expect(input).toHaveAttribute('placeholder', 'Descrição ou recebedor')
  expect(input).toHaveValue('')
  expect(screen.queryByRole('button', { name: 'Limpar busca' })).not.toBeInTheDocument()
  expect(screen.getByRole('search')).toBeInTheDocument()
})

test('does not commit before 300 ms', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  render(<SearchInput value={null} onCommit={onCommit} />)

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'acougue' } })
  vi.advanceTimersByTime(299)

  expect(onCommit).not.toHaveBeenCalled()
})

test('commits once after 300 ms without typing', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  render(<SearchInput value={null} onCommit={onCommit} />)

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'acougue' } })
  vi.advanceTimersByTime(300)

  expect(onCommit).toHaveBeenCalledTimes(1)
  expect(onCommit).toHaveBeenCalledWith('acougue')
})

test('restarts the debounce on every keystroke', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  render(<SearchInput value={null} onCommit={onCommit} />)

  const input = screen.getByLabelText('Buscar')
  fireEvent.change(input, { target: { value: 'ac' } })
  vi.advanceTimersByTime(200)
  fireEvent.change(input, { target: { value: 'aco' } })
  vi.advanceTimersByTime(200)

  expect(onCommit).not.toHaveBeenCalled()

  vi.advanceTimersByTime(100)

  expect(onCommit).toHaveBeenCalledTimes(1)
  expect(onCommit).toHaveBeenCalledWith('aco')
})

test('Enter commits immediately', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  render(<SearchInput value={null} onCommit={onCommit} />)

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'mercado' } })
  fireEvent.submit(screen.getByRole('search'))

  expect(onCommit).toHaveBeenCalledTimes(1)
  expect(onCommit).toHaveBeenCalledWith('mercado')

  vi.advanceTimersByTime(300)

  expect(onCommit).toHaveBeenCalledTimes(1)
})

test('shows the clear button only when there is text', async () => {
  const user = userEvent.setup()
  render(<SearchInput value={null} onCommit={vi.fn()} />)

  const input = screen.getByLabelText('Buscar')
  await user.type(input, 'a')

  const clearButton = screen.getByRole('button', { name: 'Limpar busca' })
  expect(clearButton).toHaveTextContent('Limpar')

  await user.clear(input)

  expect(screen.queryByRole('button', { name: 'Limpar busca' })).not.toBeInTheDocument()
})

test('clearing empties the field and commits an empty string immediately', async () => {
  const user = userEvent.setup()
  const onCommit = vi.fn()
  render(<SearchInput value="mercado" onCommit={onCommit} />)

  await user.click(screen.getByRole('button', { name: 'Limpar busca' }))

  expect(screen.getByLabelText('Buscar')).toHaveValue('')
  expect(onCommit).toHaveBeenCalledTimes(1)
  expect(onCommit).toHaveBeenCalledWith('')
})

test('starts with the value from the URL', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  render(<SearchInput value="mercado" onCommit={onCommit} />)

  expect(screen.getByLabelText('Buscar')).toHaveValue('mercado')

  vi.advanceTimersByTime(300)

  expect(onCommit).not.toHaveBeenCalled()
})

test('follows a new value from outside', () => {
  const onCommit = vi.fn()
  const { rerender } = render(<SearchInput value={null} onCommit={onCommit} />)

  rerender(<SearchInput value="posto" onCommit={onCommit} />)

  expect(screen.getByLabelText('Buscar')).toHaveValue('posto')
  expect(onCommit).not.toHaveBeenCalled()
})

test('keeps the draft when the committed value comes back from the URL', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  const { rerender } = render(<SearchInput value={null} onCommit={onCommit} />)

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'acougue' } })
  vi.advanceTimersByTime(300)
  expect(onCommit).toHaveBeenCalledWith('acougue')

  rerender(<SearchInput value="acougue" onCommit={onCommit} />)

  expect(screen.getByLabelText('Buscar')).toHaveValue('acougue')

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'acougues' } })

  expect(screen.getByLabelText('Buscar')).toHaveValue('acougues')
})

test('does not commit after unmount', () => {
  vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
  const onCommit = vi.fn()
  const { unmount } = render(<SearchInput value={null} onCommit={onCommit} />)

  fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'ac' } })
  unmount()
  vi.advanceTimersByTime(300)

  expect(onCommit).not.toHaveBeenCalled()
})
