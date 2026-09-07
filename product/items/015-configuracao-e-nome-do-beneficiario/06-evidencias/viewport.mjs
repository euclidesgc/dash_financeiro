// Mede a tela nas três larguras, de duas maneiras: carregando já naquela
// largura e redimensionando depois de carregada. São seis medições, e cada uma
// responde duas perguntas — o corpo rola de lado? algum campo desce de 16px?
//
// Uso: node <este arquivo> <url> <cookie k=v>

import { spawn } from "node:child_process";

const CHROME =
  process.env.DASH_CHROME ||
  `${process.env.HOME}/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`;
const [url, cookie] = process.argv.slice(2);
const LARGURAS = [375, 768, 1440];
const ALTURA = 800;
const MINIMO = 16;

const MEDIDA = `(() => {
  const campos = [...document.querySelectorAll("input")];
  return {
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    campos: campos.length,
    menorFonte: campos.length
      ? Math.min(...campos.map((el) => parseFloat(getComputedStyle(el).fontSize)))
      : null,
  };
})()`;

function conectar(endereco) {
  return new Promise((resolve, reject) => {
    const socket = new WebSocket(endereco);
    socket.onopen = () => resolve(socket);
    socket.onerror = reject;
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

const processo = spawn(CHROME, [
  "--headless=new",
  "--remote-debugging-port=0",
  "--no-sandbox",
  "--disable-gpu",
  // Sem --hide-scrollbars de propósito: escondida, a barra vertical não consome
  // largura, e as seis medições davam scrollWidth exatamente igual a
  // innerWidth — folga zero. O navegador do dono tem barra, e é com ela que a
  // pergunta "o corpo rola de lado?" precisa ser respondida.
  "--user-data-dir=/tmp/dash-viewport",
]);
const endereco = await new Promise((resolve, reject) => {
  let saida = "";
  processo.stderr.on("data", (pedaco) => {
    saida += pedaco;
    const achado = saida.match(/ws:\/\/[^\s]+/);
    if (achado) resolve(achado[0]);
  });
  processo.on("exit", (codigo) => reject(new Error(`navegador saiu com ${codigo}`)));
});

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
const [name, ...resto] = cookie.split("=");
await falar("Network.setCookie", {
  name,
  value: resto.join("="),
  domain: new URL(url).hostname,
  path: "/",
});

const medir = async () => {
  const { result } = await falar("Runtime.evaluate", {
    expression: MEDIDA,
    returnByValue: true,
  });
  return result.value;
};
const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const metrica = (width) =>
  falar("Emulation.setDeviceMetricsOverride", {
    width,
    height: ALTURA,
    deviceScaleFactor: 1,
    mobile: false,
  });

let reprovou = false;
for (const largura of LARGURAS) {
  for (const modo of ["carregando", "redimensionando"]) {
    if (modo === "carregando") {
      await metrica(largura);
      await falar("Page.navigate", { url });
    } else {
      await metrica(LARGURAS[0] === largura ? 1440 : LARGURAS[0]);
      await falar("Page.navigate", { url });
      await esperar(500);
      await metrica(largura);
    }
    await esperar(600);
    const lido = await medir();
    const semRolagem = lido.scrollWidth <= lido.innerWidth;
    const fonteOk = lido.campos > 0 && lido.menorFonte >= MINIMO;
    if (!semRolagem || !fonteOk) reprovou = true;
    console.log(
      `${largura}px ${modo}: scrollWidth=${lido.scrollWidth} innerWidth=${lido.innerWidth} ` +
        `semRolagem=${semRolagem} campos=${lido.campos} menorFonte=${lido.menorFonte}px ` +
        `fonteOk=${fonteOk}`,
    );
  }
}

socket.close();
processo.kill();
process.exit(reprovou ? 1 : 0);
