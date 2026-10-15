// Renders tools/og.html to img/og-v4.png (1200 x 630). Run from ../runcast,
// which has puppeteer-core: node ../arcpace-site/tools/make_og.mjs
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const puppeteer = createRequire(`${process.cwd()}/`)('puppeteer-core');
const site = fileURLToPath(new URL('..', import.meta.url));
const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--no-sandbox', '--allow-file-access-from-files'] });
const p = await b.newPage();
await p.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
await p.goto(`file://${site}tools/og.html`, { waitUntil: 'load' });
await p.waitForFunction('window.ready === true');
await p.screenshot({ path: `${site}img/og-v4.png` });
await b.close();
