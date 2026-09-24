import {readFileSync} from 'node:fs';import {evaluate,compare} from './evaluation.mjs';
const [dataset,baseline,candidate]=process.argv.slice(2);if(!dataset||!baseline)throw new Error('Usage: node eval-cli.mjs dataset.json predictions.json [shadow-predictions.json]');
const cases=JSON.parse(readFileSync(dataset)),a=JSON.parse(readFileSync(baseline));const report=evaluate(cases,a.predictions,a.model);if(candidate){const b=JSON.parse(readFileSync(candidate));report.shadow=compare(report,evaluate(cases,b.predictions,b.model))}console.log(JSON.stringify(report,null,2));
