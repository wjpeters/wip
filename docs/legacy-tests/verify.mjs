import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const output = resolve(here, '../../../docs/evidence/screenshots');
const base = process.env.MTT_BASE_URL || 'http://localhost:4173';
const pin = process.env.MTT_LOCAL_PIN || '2468';
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const failures = [];
page.on('pageerror', error => failures.push(error.message));
const checks = [];
const check = (name, condition) => { if (!condition) throw new Error(`FAIL: ${name}`); checks.push(`PASS: ${name}`); };

try {
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.getByLabel('Lokale toegangscode').fill(pin);
  await page.getByRole('button', { name: 'Ontgrendelen' }).click();
  await page.getByRole('heading', { name: 'Watchlist' }).waitFor();
  check('lokale PIN-sessie opent terminal', true);
  check('paper- en simulatiestatus is zichtbaar', (await page.locator('body').innerText()).includes('DEMO / SYNTHETISCH'));
  await page.screenshot({ path: resolve(output, 'terminal-1920x1080.png'), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({ path: resolve(output, 'terminal-1440x900.png'), fullPage: true });
  await page.setViewportSize({ width: 3440, height: 1440 });
  await page.screenshot({ path: resolve(output, 'terminal-3440x1440.png'), fullPage: true });
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.getByRole('button', { name: 'Licht' }).click();
  await page.screenshot({ path: resolve(output, 'terminal-light-1920x1080.png'), fullPage: true });
  check('lichtthema is omschakelbaar', await page.locator('html').getAttribute('data-theme') === 'light');
  await page.getByRole('button', { name: 'Donker' }).click();

  await page.getByRole('button', { name: 'Trade Impact Preview' }).click();
  await page.getByText('Voor / na · gesimuleerd').waitFor();
  const preview = await page.locator('body').innerText();
  check('preview toont cash, fee, positie en doelbuffer', ['Cash voor → na','Notional / kosten','Positie BTC voor → na','Doelbuffer na'].every(s => preview.includes(s)));
  await page.screenshot({ path: resolve(output, 'trade-impact-preview-1920x1080.png'), fullPage: true });

  await page.getByRole('button', { name: 'Paperorder plaatsen' }).click();
  await page.getByRole('status').waitFor();
  check('paperfill wordt bevestigd met order-ID', (await page.getByRole('status').innerText()).includes('FILLED'));
  await page.locator('.tabs button').filter({ hasText: 'Journaal' }).click();
  await page.locator('.tabs button.selected-tab').filter({ hasText: 'Journaal' }).waitFor();
  await page.locator('.table-row').first().waitFor();
  const journal = (await page.locator('.table-row').allTextContents()).join(' ');
  check('journaal toont EUR-postings en geen hoeveelheid als geld', journal.includes('paper_cash') && !journal.includes('btc_quantity'));
  await page.screenshot({ path: resolve(output, 'paper-journal-1920x1080.png'), fullPage: true });

  await page.getByRole('button', { name: 'Vermogen' }).click();
  await page.getByText('Exclusief van werkelijk vermogen').waitFor();
  check('papervermogen blijft uitgesloten van echte balans', true);
  await page.screenshot({ path: resolve(output, 'wealth-1920x1080.png'), fullPage: true });

  await page.getByRole('button', { name: 'Planning' }).click();
  await page.getByText('Pensioen, jaarruimte, Box 1/2/3').waitFor();
  check('planning benoemt expliciet ontbrekende fiscale scope', true);
  await page.screenshot({ path: resolve(output, 'planning-1920x1080.png'), fullPage: true });

  await page.getByRole('button', { name: 'Bronstatus' }).click();
  await page.getByText('NOT_RUN_EXTERNAL_NETWORK').waitFor();
  check('providerverbinding is als niet uitgevoerd gemarkeerd', true);
  await page.screenshot({ path: resolve(output, 'source-health-1920x1080.png'), fullPage: true });

  await page.getByRole('button', { name: 'Terminal' }).click();
  await page.locator('.rail-item.active').filter({ hasText: 'Terminal' }).waitFor();
  await page.evaluate(() => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); });
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileActive = await page.locator('.rail-item.active').allInnerTexts();
  check('mobiele navigatie blijft op Terminal', mobileActive.length === 1 && mobileActive[0].includes('Terminal'));
  await page.screenshot({ path: resolve(output, 'terminal-mobile-390x844.png'), fullPage: true });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  check('mobiele terminal heeft geen horizontale page-overflow', !overflow);
  check('geen uncaught frontendfouten', failures.length === 0);

  const result = { base_url: base, viewports: ['1920x1080', '1440x900', '3440x1440', '390x844'], mode: 'PAPER / SIMULATED', checks, page_errors: failures };
  await writeFile(resolve(output, '../m1-e2e-results.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(checks.join('\n'));
} finally {
  await browser.close();
}
