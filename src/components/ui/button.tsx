import type { ComponentPropsWithRef } from 'react'

export type ButtonProps = ComponentPropsWithRef<'button'> & {
  variant?: 'primary' | 'secondary' | 'danger'
}

const VARIANT_CLASSES = {
  primary:
    'rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50',
  secondary:
    'rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50',
  danger:
    'rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50',
} as const

export function Button({
  variant = 'primary',
  type = 'button',
  className,
  ref,
  ...rest
}: ButtonProps): React.JSX.Element {
  const classes = [VARIANT_CLASSES[variant], 'min-h-10', className].filter(Boolean).join(' ')

  return <button ref={ref} type={type} className={classes} {...rest} />
}
