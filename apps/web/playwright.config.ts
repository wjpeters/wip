import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',timeout:45000,fullyParallel:false,workers:1,
 reporter:[['list'],['json',{outputFile:'../../docs/evidence/e2e-results.json'}]],
 use:{baseURL:process.env.MTT_TEST_URL||'http://localhost:4187',viewport:{width:1920,height:1080},trace:'retain-on-failure'},
 projects:[{name:'chromium',use:{browserName:'chromium'}},{name:'webkit',use:{browserName:'webkit'}}]});
