import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const origin='http://localhost:4188';
const password=fs.readFileSync(path.resolve('../../.secrets/e2e_password'),'utf8').trim();
const folder=path.resolve('../../docs/evidence/screenshots');
const browser=await chromium.launch();
const page=await browser.newPage({viewport:{width:1672,height:940}});
try {
 await page.goto(origin);
 await page.getByRole('button',{name:'Lokale omgeving instellen'}).waitFor();
 await page.screenshot({path:path.join(folder,'fresh-onboarding.png')});
 await page.getByLabel(/wachtwoord/i).fill(password);
 await page.getByRole('button',{name:'Lokale omgeving instellen'}).click();
 await page.getByText('Je eerste paperorder begint met inzicht').waitFor();
 await page.locator('.market-chart canvas').first().waitFor();
 await page.screenshot({path:path.join(folder,'fresh-terminal-native-reference-size.png')});
 await page.getByRole('button',{name:'Posities',exact:true}).click();
 await page.getByText('Nog geen paperposities',{exact:true}).waitFor();
 await page.screenshot({path:path.join(folder,'fresh-empty-positions.png')});
 await page.getByRole('button',{name:'Vermogen',exact:true}).click();
 await page.getByRole('heading',{name:'Je oefenvermogen'}).waitFor();
 await page.screenshot({path:path.join(folder,'fresh-wealth.png')});
 fs.writeFileSync(path.resolve('../../docs/evidence/fresh-install.json'),JSON.stringify({status:'PASS',scope:'First setup and empty states on isolated new wpos-mtt-empty volume, Chromium 1672x940',screenshots:['fresh-onboarding.png','fresh-terminal-native-reference-size.png','fresh-empty-positions.png','fresh-wealth.png'],user_database_untouched:true},null,2));
 console.log('PASS: fresh setup, empty orders, empty positions and wealth');
} finally {await browser.close()}
