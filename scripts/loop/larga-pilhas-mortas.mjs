#!/usr/bin/env node
/* Larga o rastreamento local das pilhas cujos PRs já não estão abertos.

   ## O problema que ele existe para impedir

   `gh stack` guarda cada pilha em `.git/gh-stack`, e nada as remove quando
   elas cumprem o papel. Uma corrida autônoma cria uma pilha por estágio e por
   fase, e nenhuma é largada — então o arquivo acumula pilhas mortas, todas com
   o mesmo trunk. Na terceira, `gh stack add` recusa:

       ✗ branch "develop" belongs to multiple stacks;
         use an interactive terminal to select one

   Não há flag que escolha entre pilhas, e `gh stack init` cria mais uma. Numa
   corrida não há terminal interativo, então a rodada morre sem branch. E o
   problema piora sozinho a cada estágio que fecha: quem esbarrou nele com três
   pilhas vai esbarrar com quatro na sessão seguinte.

   ## Por que ele mede antes de largar

   Largar uma pilha viva é perder a corrente de PRs que ainda vão mergear. Por
   isso cada PR é medido no GitHub, e a pilha só é largada quando **nenhum**
   deles está aberto. Não conseguir medir um PR preserva a pilha inteira — a
   dúvida é a favor de manter, porque manter custa um aviso e largar custa a
   corrente.

   Nunca larga a pilha que contém a branch corrente, mesmo morta: é a que a
   sessão pode estar usando agora.

   Só mexe no rastreamento **local**, como `gh stack unstack --local`: o que
   está no GitHub fica intacto. E copia o arquivo antes de reescrever.

   ## Uso

   `node scripts/loop/larga-pilhas-mortas.mjs [--root <dir>] [--dry-run]`
   Sai 0 quando decidiu (tendo largado ou não) e 1 quando não conseguiu medir. */

import { execFileSync } from 'node:child_process';
import { copyFileSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ_PADRAO = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const TETO_MS = 30_000;

/* O formato é interno do `gh stack`. Mexer nele exige reconhecê-lo primeiro:
   schema diferente do conhecido é motivo para não tocar, nunca para adivinhar. */
const SCHEMA_CONHECIDO = 1;

export const pilhasMortas = (dados, estadoDoPr, branchCorrente) => {
  const vivas = [];
  const largadas = [];
  const naoMedidas = [];

  for (const pilha of dados.stacks ?? []) {
    const branches = pilha.branches ?? [];
    const contemCorrente = branches.some((b) => b.branch === branchCorrente);
    const prs = branches.map((b) => b.pullRequest?.number).filter((n) => Number.isInteger(n));

    if (contemCorrente || prs.length === 0 || prs.length !== branches.length) {
      vivas.push(pilha);
      continue;
    }

    const estados = prs.map((n) => ({ pr: n, estado: estadoDoPr(n) }));
    const ilegivel = estados.find((e) => !e.estado);
    if (ilegivel) {
      naoMedidas.push(`#${ilegivel.pr}`);
      vivas.push(pilha);
      continue;
    }
    if (estados.every((e) => e.estado === 'MERGED' || e.estado === 'CLOSED')) {
      largadas.push({ prs, trunk: pilha.trunk?.branch ?? '?' });
    } else {
      vivas.push(pilha);
    }
  }

  return { vivas, largadas, naoMedidas };
};

const gh = (args) => {
  try {
    return execFileSync('gh', args, { encoding: 'utf-8', timeout: TETO_MS }).trim();
  } catch {
    return '';
  }
};

const branchAtual = (root) => {
  try {
    return execFileSync('git', ['-C', root, 'branch', '--show-current'], {
      encoding: 'utf-8',
      timeout: TETO_MS,
    }).trim();
  } catch {
    return '';
  }
};

const isMain = process.argv[1] && resolve(process.argv[1]) === resolve(fileURLToPath(import.meta.url));
if (isMain) {
  const flag = process.argv.indexOf('--root');
  const root = flag === -1 ? RAIZ_PADRAO : resolve(process.argv[flag + 1]);
  const seco = process.argv.includes('--dry-run');
  const arquivo = join(root, '.git', 'gh-stack');

  if (!existsSync(arquivo)) {
    console.log('pilhas: .git/gh-stack não existe — nada rastreado, nada a largar.');
    process.exit(0);
  }

  let dados;
  try {
    dados = JSON.parse(readFileSync(arquivo, 'utf-8'));
  } catch (erro) {
    console.error(`pilhas: .git/gh-stack ilegível (${erro.message}) — não mexo no que não li.`);
    process.exit(1);
  }

  if (dados.schemaVersion !== SCHEMA_CONHECIDO) {
    console.error(
      `pilhas: .git/gh-stack está no schema ${dados.schemaVersion}, e eu só conheço o ${SCHEMA_CONHECIDO}.`,
    );
    console.error('pilhas: não mexo num formato que não reconheço. Largue à mão com `gh stack unstack --local`.');
    process.exit(1);
  }

  const total = (dados.stacks ?? []).length;
  const { vivas, largadas, naoMedidas } = pilhasMortas(
    dados,
    (numero) => gh(['pr', 'view', String(numero), '--json', 'state', '--jq', '.state']),
    branchAtual(root),
  );

  console.log(`medido: ${total} pilha(s) rastreada(s) em .git/gh-stack, ${largadas.length} morta(s).`);
  for (const nome of naoMedidas) {
    console.error(`pilhas: não consegui medir o PR ${nome} — mantenho a pilha dele. A dúvida é a favor de manter.`);
  }
  if (largadas.length === 0) process.exit(0);

  for (const morta of largadas) {
    console.log(`pilhas: largando a de trunk ${morta.trunk} — PRs ${morta.prs.map((n) => `#${n}`).join(', ')}, nenhum aberto.`);
  }
  if (seco) {
    console.log('pilhas: --dry-run, nada foi escrito.');
    process.exit(0);
  }

  copyFileSync(arquivo, `${arquivo}.bak`);
  writeFileSync(arquivo, `${JSON.stringify({ ...dados, stacks: vivas }, null, 2)}\n`);
  console.log(`pilhas: ${largadas.length} largada(s) só no rastreamento local; o GitHub não foi tocado. Cópia em .git/gh-stack.bak`);
}
