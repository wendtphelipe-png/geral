// Converte os SVG de fichas/ em PNG (usa o Chromium do Playwright).
// Uso: node renderizar.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const pasta = path.join(__dirname, 'fichas');
  const navegador = await chromium.launch();
  const pagina = await navegador.newPage();
  for (const nome of fs.readdirSync(pasta).filter(f => f.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(pasta, nome), 'utf8');
    const [, l, a] = svg.match(/viewBox="0 0 (\d+) (\d+)"/);
    await pagina.setViewportSize({ width: +l, height: +a });
    await pagina.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await pagina.screenshot({ path: path.join(pasta, nome.replace('.svg', '.png')) });
  }
  await navegador.close();
})();
