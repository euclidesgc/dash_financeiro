export function MissingKeyNotice({ message }: { message: string | null }): React.JSX.Element {
  return (
    <section
      aria-labelledby="missing-key-heading"
      className="mt-6 rounded-md border border-amber-200 bg-amber-50 p-4"
    >
      <h2 id="missing-key-heading" className="font-semibold text-amber-900">
        Falta a chave da IA
      </h2>
      <p className="mt-2 text-amber-900">
        {message ?? 'O consultor precisa de uma chave de IA para responder.'}
      </p>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-amber-900">
        <li>
          Anthropic: coloque <code className="font-mono">ANTHROPIC_API_KEY</code> no arquivo{' '}
          <code className="font-mono">.env</code> e reinicie o painel.
        </li>
        <li>
          Gemini: coloque <code className="font-mono">GEMINI_API_KEY</code> no{' '}
          <code className="font-mono">.env</code> ou informe a chave na tela{' '}
          <a href="/configuracao" className="font-medium text-blue-600 underline-offset-4 hover:underline">
            Configuração
          </a>
          .
        </li>
      </ul>
    </section>
  )
}
