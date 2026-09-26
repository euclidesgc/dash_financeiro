export const advisorKeys = {
  status: ['advisor', 'status'] as const,
  conversations: ['advisor', 'conversations'] as const,
  conversation: (id: number) => ['advisor', 'conversation', id] as const,
}
