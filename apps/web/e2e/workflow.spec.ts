import {test,expect,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
import path from 'node:path';
const password=fs.readFileSync(path.resolve('../../.secrets/e2e_password'),'utf8').trim();
const evidence=path.resolve('../../docs/evidence/screenshots');fs.mkdirSync(evidence,{recursive:true});
async function login(page:Page){
 await page.goto('/');await expect(page.getByLabel(/wachtwoord/i)).toBeVisible();
 await page.getByLabel(/wachtwoord/i).fill(password);
 await page.getByRole('button',{name:/Ontgrendelen|Lokale omgeving instellen/}).click();
 await expect(page.getByRole('navigation',{name:'Hoofdnavigatie'})).toBeVisible();
}
async function screen(page:Page,name:string,project:string){await page.screenshot({path:path.join(evidence,`${project}-${name}.png`),fullPage:true})}
test('complete paperworkflow, bronnen, preview, ledger en plan',async({page},info)=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await login(page);await expect(page).toHaveTitle('Modern Trade Terminal');
 await page.getByRole('button',{name:'Terminal',exact:true}).click();
 await page.locator('.watch-row').filter({hasText:'ETH'}).click();await expect(page.getByRole('heading',{name:'ETH/EUR',exact:true}).first()).toBeVisible();
 await page.locator('.watch-row').filter({hasText:'BTC'}).click();
 await page.getByRole('button',{name:'Bron inspecteren',exact:false}).click();
 await expect(page.getByRole('dialog')).toContainText('mtt-synthetic-v1');
 await page.getByRole('button',{name:'Lokale contracttest',exact:true}).click();await expect(page.getByRole('status')).toContainText('TESTED_WITH_FIXTURES');
 await page.getByRole('button',{name:'Sluiten',exact:true}).click();
 await page.getByRole('button',{name:'15m',exact:true}).click();await expect(page.getByRole('button',{name:'15m',exact:true})).toHaveAttribute('aria-pressed','true');
 await page.getByLabel('SMA 20').uncheck();await page.getByLabel('SMA 20').check();
 await page.getByRole('button',{name:'1u',exact:true}).click();
 await expect(page.locator('.market-chart canvas').first()).toBeVisible();
 await screen(page,'terminal-1920x1080',info.project.name);
 await page.getByLabel('Aantal (BTC)',{exact:true}).fill('0.0100');await page.getByLabel('Limietprijs (EUR)',{exact:true}).fill('62500.00');
 await page.getByRole('button',{name:'Trade Impact Preview',exact:false}).click();
 const dialog=page.getByRole('dialog');await expect(dialog).toContainText('Trade Impact Preview');
 await expect(dialog).toContainText('€ 1,00');await expect(dialog).toContainText('paperdata is geen fiscaal feit');
 await screen(page,'trade-impact',info.project.name);
 await page.getByRole('button',{name:'Paperorder plaatsen',exact:true}).click();
 await expect(dialog).not.toBeVisible();await expect(page.getByRole('status')).toContainText('FILLED');
 await expect(page.getByRole('region',{name:'Paperjournaal'})).toContainText('inventory:sim:BTC-EUR');
 await screen(page,'journaal',info.project.name);
 await page.getByRole('button',{name:'Melding sluiten'}).click();
 await page.getByRole('button',{name:'Vermogen',exact:true}).click();await expect(page.getByRole('heading',{name:'Je oefenvermogen'})).toBeVisible();
 await expect(page.getByRole('region',{name:'Rekeningen en posities'})).toContainText('BTC-EUR');await screen(page,'vermogen',info.project.name);
 await page.getByRole('button',{name:'Planning',exact:true}).click();const reserve=page.getByLabel('Doelreserve (EUR)',{exact:true});await reserve.fill((await reserve.inputValue())==='25000.00'?'26000.00':'25000.00');
 await page.getByRole('button',{name:'Oefenplan opslaan'}).click();await expect(page.getByText('Oefenplan opgeslagen.',{exact:true})).toBeVisible();
 await screen(page,'planning',info.project.name);
 await page.getByRole('button',{name:'Bronnen',exact:true}).click();await expect(page.getByRole('region',{name:'Bronstatus'})).toContainText('NOT_RUN_EXTERNAL_NETWORK');
 await screen(page,'bronnen',info.project.name);
 await page.getByRole('button',{name:'Inspecteer Lokale simulatie'}).click();await page.getByRole('button',{name:'Bron pauzeren',exact:true}).click();
 await page.getByRole('button',{name:'Terminal',exact:true}).click();await expect(page.getByRole('button',{name:'Trade Impact Preview',exact:false})).toBeDisabled();await expect(page.locator('.stale-banner')).toBeVisible();
 await screen(page,'storing',info.project.name);
 await page.getByRole('button',{name:'Bron inspecteren',exact:false}).click();await page.getByRole('button',{name:'Bron hervatten'}).click();
 await page.getByRole('button',{name:'Assistent',exact:true}).click();await expect(page.getByText('LOKALE UITLEG · GEEN AI')).toBeVisible();await screen(page,'uitleg',info.project.name);
 await page.getByRole('button',{name:'Order',exact:true}).click();
 await page.keyboard.press('Control+k');await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('textbox',{name:'Zoeken',exact:true}).fill('ETH');
 await page.getByRole('dialog').getByRole('button',{name:/ETH\/EUR/}).click();await expect(page.getByRole('heading',{name:'ETH/EUR',exact:true}).first()).toBeVisible();
 await page.reload();await expect(page.getByRole('heading',{name:'ETH/EUR',exact:true}).first()).toBeVisible();
 expect(errors).toEqual([]);
});
test('responsive, thema, reduced motion, keyboard en toegankelijkheid',async({page},info)=>{
 await login(page);await page.getByRole('button',{name:'Terminal',exact:true}).click();
 await page.emulateMedia({reducedMotion:'reduce'});
 for(const [width,height] of [[1440,900],[1920,1080],[3440,1440],[1024,768],[390,844]]){
  await page.setViewportSize({width,height});
  await expect(page.locator('.market-chart canvas').first()).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  if(width===390){await expect(page.getByLabel(/^Aantal /)).toBeDisabled();await expect(page.getByText(/Mobiele leesmodus/)).toBeVisible()}
  await screen(page,`terminal-${width}x${height}`,info.project.name);
 }
 await page.setViewportSize({width:1920,height:1080});
 await page.getByRole('button',{name:'Thema wisselen'}).click();await expect(page.locator('html')).toHaveAttribute('data-theme','light');
 await screen(page,'terminal-light',info.project.name);
 const light=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(light.violations).toEqual([]);
 await page.getByRole('button',{name:'Thema wisselen'}).click();
 const dark=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(dark.violations).toEqual([]);
 await page.keyboard.press('Control+k');await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).not.toBeVisible();
 // A 960px CSS viewport verifies reflow corresponding to 200% zoom on a 1920px display; this is not a native browser zoom test.
 await page.setViewportSize({width:960,height:540});await screen(page,'reflow-200-percent',info.project.name);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
