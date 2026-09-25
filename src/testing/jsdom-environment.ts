import { builtinEnvironments, type Environment } from 'vitest/environments'

// Reason: jsdom replaces AbortController/AbortSignal with its own, but leaves
// Request to Node's undici, which only accepts Node's AbortSignal. React
// Router's data router builds `new Request(url, { signal })` on every
// navigation, so the two globals must come from the same realm.
const { AbortController, AbortSignal } = globalThis

const jsdomWithNodeAbort: Environment = {
  name: 'jsdom-node-abort',
  transformMode: 'web',
  async setup(global: typeof globalThis, options) {
    const environment = await builtinEnvironments.jsdom.setup(global, options)
    global.AbortController = AbortController
    global.AbortSignal = AbortSignal
    return environment
  },
}

export default jsdomWithNodeAbort
