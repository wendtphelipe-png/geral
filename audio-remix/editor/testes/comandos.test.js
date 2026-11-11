// Rodar: node editor/testes/comandos.test.js
const assert = require("assert");
const {entender, aplicar} = require("../public/comandos.js");
const bloco = () => ({u: "o1", faixas: {voz: 1, bateria: 1, baixo: 1, outros: 1}, vel: 1});
const ctx = {dur: b => 4 * ((b.ate ?? 1) - (b.de ?? 0)) / b.vel, tempo: 0.5};
function rodar(texto, n = 2) {
  const tl = Array.from({length: 4}, bloco);
  const r = entender(texto);
  const sel = aplicar(tl, [...Array(n).keys()], r.acoes, ctx);
  return {tl, r, sel};
}
const casos = [
  ["tira a voz desse trecho", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 0, bateria: 1, baixo: 1, outros: 1})],
  ["quero que tire a voz do artista, deixe apenas os instrumentos", ({tl}) => assert.deepStrictEqual(tl[1].faixas, {voz: 0, bateria: 1, baixo: 1, outros: 1})],
  ["só a voz", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 1, bateria: 0, baixo: 0, outros: 0})],
  ["nesta contagem de 8, quero mais batidas graves", ({tl}) => { assert.ok(tl[0].faixas.baixo > 1); assert.ok(tl[0].faixas.bateria > 1); assert.strictEqual(tl[0].faixas.voz, 1); }],
  ["voz 30% mais baixa", ({tl}) => assert.ok(Math.abs(tl[0].faixas.voz - 0.7) < 1e-9)],
  ["aumenta o baixo em 20%", ({tl}) => assert.ok(Math.abs(tl[0].faixas.baixo - 1.2) < 1e-9)],
  ["deixa a bateria em 50%", ({tl}) => assert.strictEqual(tl[0].faixas.bateria, 0.5)],
  ["sem bateria e sem baixo", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 1, bateria: 0, baixo: 0, outros: 1})],
  ["meio tempo", ({tl}) => assert.strictEqual(tl[1].vel, 0.5)],
  ["coloca em tempo dobrado", ({tl}) => assert.strictEqual(tl[0].vel, 2)],
  ["repete esses oitos 2 vezes", ({tl}) => assert.strictEqual(tl.length, 8)],
  ["apaga esses oitos", ({tl, sel}) => { assert.strictEqual(tl.length, 2); assert.strictEqual(sel.length, 0); }],
  ["volta a voz", ({tl}) => assert.strictEqual(tl[0].faixas.voz, 1)],
  ["adicione nesse trecho a voz do artista que ele usa no oito 5, e coloque como um eco distante com volume 30% mais baixo", ({r}) => {
    assert.strictEqual(r.acoes.length, 1); const a = r.acoes[0];
    assert.strictEqual(a.tipo, "trazer"); assert.strictEqual(a.faixa, "voz"); assert.strictEqual(a.oito, "5");
    assert.ok(a.fx.distante && a.fx.eco > 0 && a.fx.reverb > 0 && a.fx.filtro === "abafado"); assert.ok(Math.abs(a.ganho - 0.7) < 1e-9); }],
  ["eco na voz", ({tl}) => { assert.ok(tl[0].fx.voz.eco > 0); assert.strictEqual(tl[0].fx.tudo, undefined); }],
  ["muito reverb", ({tl}) => assert.strictEqual(tl[1].fx.tudo.reverb, 0.75)],
  ["deixa a bateria com som de rádio", ({tl}) => assert.strictEqual(tl[0].fx.bateria.filtro, "radio")],
  ["deixa tudo distante", ({tl}) => { assert.ok(tl[0].fx.tudo.distante); assert.ok(tl[0].faixas.voz < 1); }],
  ["tira o eco", ({tl}) => assert.strictEqual(tl[0].fx, undefined)],
  ["parada no 5 e no 7", ({tl}) => assert.deepStrictEqual(tl[0].paradas, [[4, 0.5], [6, 0.5]])],
  ["freeze no tempo 1 de 2 tempos", ({tl}) => assert.deepStrictEqual(tl[1].paradas, [[0, 2]])],
  ["stop", ({tl}) => assert.deepStrictEqual(tl[0].paradas, [[7, 0.5]])],
  ["tira as paradas", ({tl}) => assert.strictEqual(tl[0].paradas, undefined)],
  ["sem eco e meio tempo", ({tl}) => assert.strictEqual(tl[0].vel, 0.5)],
  ["transforma em house", ({r}) => assert.ok(r.faltando.includes("injetar estilo"))],
  ["tira a voz e deixa o grave 30% mais alto", ({tl}) => { assert.strictEqual(tl[0].faixas.voz, 0); assert.ok(Math.abs(tl[0].faixas.baixo - 1.3) < 1e-9); }],
  ["coloca a voz do oito 5 como eco distante", ({r}) => { assert.strictEqual(r.acoes[0].tipo, "trazer"); assert.strictEqual(r.acoes[0].ganho, 1); }],
  ["tira a voz do oito 3", ({tl}) => assert.strictEqual(tl[0].faixas.voz, 0)],
  ["tira a bateria, meio tempo", ({tl}) => { assert.strictEqual(tl[0].faixas.bateria, 0); assert.strictEqual(tl[0].vel, 0.5); }],
  ["só voz e bateria", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 1, bateria: 1, baixo: 0, outros: 0})],
  ["tira a voz e o baixo", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 0, bateria: 1, baixo: 0, outros: 1})],
  ["fade out", ({tl}) => { assert.strictEqual(tl[0].env[0][1], 1); assert.ok(tl[1].env[12][1] < 1e-6); assert.ok(tl[0].env[12][1] > 0.4 && tl[0].env[12][1] < 0.6); }],
  ["fade in de 2 tempos", ({tl}) => { assert.ok(tl[0].env[0][1] < 1e-6); assert.ok(Math.abs(tl[0].env[3][1] - 1) < 1e-6); assert.strictEqual(tl[1].env, undefined); }],
  ["faz a música sumir aos poucos", ({r}) => assert.ok(r.acoes.length === 0 || r.acoes[0].tipo === "fade")],
  ["corta ao meio", ({tl, sel}) => { assert.strictEqual(tl.length, 6); assert.deepStrictEqual([tl[0].de, tl[0].ate, tl[1].de, tl[1].ate], [0, 0.5, 0.5, 1]); assert.deepStrictEqual(sel, [0, 1, 2, 3]); }],
  ["corta a voz", ({tl}) => { assert.strictEqual(tl.length, 4); assert.strictEqual(tl[0].faixas.voz, 0); }],
  ["volta ao original", ({tl}) => { assert.strictEqual(tl[0].env, undefined); assert.strictEqual(tl[0].faixas.voz, 1); }],
  ["tira a voz e eco na bateria", ({tl, r}) => { assert.strictEqual(tl[0].faixas.voz, 0); assert.ok(tl[0].fx.bateria.eco > 0); assert.strictEqual(tl[0].fx.tudo, undefined); assert.strictEqual(r.frases.length, 2); }],
  ["sem efeitos", ({tl}) => assert.strictEqual(tl[0].fx, undefined)],
  ["tira todos os efeitos da voz", ({r}) => assert.strictEqual(r.acoes[0].tipo, "semFx")],
  ["só instrumental", ({tl}) => assert.deepStrictEqual(tl[0].faixas, {voz: 0, bateria: 1, baixo: 1, outros: 1})],
];
let ok = 0;
for (const [texto, conferir] of casos) {
  try { conferir(rodar(texto)); ok++; } catch (e) { console.log("FALHOU:", texto, "->", JSON.stringify(entender(texto))); }
}
console.log(`${ok}/${casos.length} comandos entendidos certo`);
process.exit(ok === casos.length ? 0 : 1);
