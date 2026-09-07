// Captura de tela das telas do painel, parametrizada por item, tela e larguras.
//
// POR QUE O HARNESS ENTREGA ESTE SCRIPT
// Ele era recriado à mão a cada item, e num projeto real quatro capturas foram
// escritas num diretório que não existia: o comando saía com código zero e o
// arquivo não aparecia. A causa raiz não era o comando — era o script não morar
// no repositório. Instrumento que o critério estrutural cobra, o harness
// entrega.
//
// POR QUE ELE NÃO USA PLAYWRIGHT
// Ele precisa rodar em projeto que não tem package.json e não pode ganhar
// dependência não declarada. O Chromium do Playwright já costuma estar na
// máquina, e o Node 24 traz WebSocket embutido, então o script fala o protocolo
// do navegador direto. `DASH_CHROME` aponta outro binário quando preciso.
//
// Uso:
//   node scripts/capturas.mjs --item 015-... --url http://127.0.0.1:8015/configuracao \
//     --nome configuracao --larguras 375,768,1440 --escuro 1440 [--cookie k=v] \
//     [--altura 900] [--seletor '#beneficiarios']
//
// --seletor recorta a captura no elemento pedido, para a imagem de um bloco
// mostrar o bloco e não a tela inteira com ele em algum lugar.

import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const CHROME =
  process.env.DASH_CHROME ||
  join(
    process.env.HOME,
    ".cache/ms-playwright/chromium-1234/chrome-linux64/chrome",
  );
const ALTURA_PADRAO = 900;

function argumentos(argv) {
  const lidos = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!argv[i].startsWith("--")) throw new Error(`argumento solto: ${argv[i]}`);
    lidos[argv[i].slice(2)] = argv[i + 1];
  }
  return lidos;
}

function conectar(endereco) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(endereco);
    socket.onopen = () => resolve(socket);
    socket.onerror = (erro) => reject(erro);
  });
}

function conversa(socket) {
  let proximo = 0;
  const pendentes = new Map();
  socket.onmessage = ({ data }) => {
    const resposta = JSON.parse(data);
    const espera = pendentes.get(resposta.id);
    if (!espera) return;
    pendentes.delete(resposta.id);
    if (resposta.error) espera.reject(new Error(JSON.stringify(resposta.error)));
    else espera.resolve(resposta.result);
  };
  return (method, params = {}, sessionId) =>
    new Promise((resolve, reject) => {
      const id = ++proximo;
      pendentes.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
}

async function navegador() {
  const processo = spawn(CHROME, [
    "--headless=new",
    "--remote-debugging-port=0",
    "--no-sandbox",
    "--disable-gpu",
    "--hide-scrollbars",
    // Um perfil fixo trava quando uma execução anterior não morreu, e o
    // navegador sai com código 21 sem dizer por quê.
    `--user-data-dir=${mkdtempSync(join(tmpdir(), "dash-capturas-"))}`,
  ]);
  const endereco = await new Promise((resolve, reject) => {
    let saida = "";
    const prazo = setTimeout(() => reject(new Error("o navegador não abriu")), 30000);
    processo.stderr.on("data", (pedaco) => {
      saida += pedaco;
      const achado = saida.match(/ws:\/\/[^\s]+/);
      if (achado) {
        clearTimeout(prazo);
        resolve(achado[0]);
      }
    });
    processo.on("exit", (codigo) => {
      clearTimeout(prazo);
      reject(new Error(`o navegador saiu com ${codigo}: ${saida}`));
    });
  });
  return { processo, endereco };
}

async function caixa(falar, seletor) {
  const { result } = await falar("Runtime.evaluate", {
    expression: `(() => {
      const alvo = document.querySelector(${JSON.stringify(seletor)});
      if (!alvo) return null;
      const caixa = alvo.getBoundingClientRect();
      return {
        x: caixa.left + window.scrollX,
        y: caixa.top + window.scrollY,
        width: caixa.width,
        height: caixa.height,
        scale: 1,
      };
    })()`,
    returnByValue: true,
  });
  if (!result.value) throw new Error(`seletor sem elemento: ${seletor}`);
  return result.value;
}

async function main() {
  const opcoes = argumentos(process.argv.slice(2));
  for (const exigido of ["item", "url", "nome", "larguras"]) {
    if (!opcoes[exigido]) throw new Error(`falta --${exigido}`);
  }
  const pasta = join(RAIZ, "product", "items", opcoes.item, "06-capturas");
  // O diretório é criado antes de qualquer captura: escrever em diretório
  // inexistente é o erro que este script existe para não repetir.
  await mkdir(pasta, { recursive: true });

  const largura = opcoes.larguras.split(",").map(Number);
  const altura = Number(opcoes.altura || ALTURA_PADRAO);
  const escuro = opcoes.escuro ? Number(opcoes.escuro) : null;
  const { processo, endereco } = await navegador();
  const socket = await conectar(endereco);
  const enviar = conversa(socket);

  const alvo = await enviar("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await enviar("Target.attachToTarget", {
    targetId: alvo.targetId,
    flatten: true,
  });
  const falar = (method, params) => enviar(method, params, sessionId);
  await falar("Page.enable");
  await falar("Network.enable");
  if (opcoes.cookie) {
    const [name, ...resto] = opcoes.cookie.split("=");
    const { hostname } = new URL(opcoes.url);
    await falar("Network.setCookie", {
      name,
      value: resto.join("="),
      domain: hostname,
      path: "/",
    });
  }

  const escritos = [];
  const tarefas = largura.map((valor) => ({ valor, tema: "light" }));
  if (escuro) tarefas.push({ valor: escuro, tema: "dark" });

  for (const { valor, tema } of tarefas) {
    await falar("Emulation.setDeviceMetricsOverride", {
      width: valor,
      height: altura,
      deviceScaleFactor: 1,
      mobile: valor < 768,
    });
    await falar("Emulation.setEmulatedMedia", {
      features: [{ name: "prefers-color-scheme", value: tema }],
    });
    await falar("Page.navigate", { url: opcoes.url });
    await new Promise((resolve) => setTimeout(resolve, 700));
    const recorte = opcoes.seletor ? await caixa(falar, opcoes.seletor) : undefined;
    const { data } = await falar("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: true,
      ...(recorte ? { clip: recorte } : {}),
    });
    const sufixo = tema === "dark" ? `dark-${valor}` : `${valor}`;
    const arquivo = join(pasta, `${opcoes.nome}-${sufixo}.png`);
    await writeFile(arquivo, Buffer.from(data, "base64"));
    escritos.push(arquivo);
  }

  socket.close();
  processo.kill();
  for (const arquivo of escritos) console.log(arquivo);
}

main().catch((erro) => {
  console.error(erro.message);
  process.exit(1);
});
