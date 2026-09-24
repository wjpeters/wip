import {hash} from './policy.mjs';
export function evaluate(cases,predictions,model){
 const tasks={};let unknown=0;
 const byId=new Map();for(const p of predictions){if(byId.has(p.id))throw new Error('DUPLICATE_PREDICTION');byId.set(p.id,p);if(!cases.some(c=>c.id===p.id))unknown++;}
 for(const c of cases){const task=tasks[c.task]??={total:0,scored:0,abstained:0,invalid:0,correct:0,absolute_error:0};task.total++;const p=byId.get(c.id);
 if(!p||p.disposition==='ABSTAIN'){task.abstained++;continue}
 if(p.model!==model){task.invalid++;continue}
 if(c.task==='news_kind'){if(!['MACRO','EARNINGS','TECHNOLOGY','OTHER'].includes(p.value)){task.invalid++;continue}task.correct+=p.value===c.label?1:0;}
 else{if(typeof p.value!=='number'||!Number.isFinite(p.value)||p.value<0||p.value>(c.task==='source_support'?1:2)){task.invalid++;continue}task.absolute_error+=Math.abs(p.value-c.label);}
 task.scored++;
 }
 for(const [name,t] of Object.entries(tasks)){t.coverage=t.scored/t.total;t.accuracy=name==='news_kind'&&t.scored?t.correct/t.scored:null;t.mean_absolute_error=name!=='news_kind'&&t.scored?t.absolute_error/t.scored:null;}
 return {schema_version:1,model_version:model,dataset_hash:hash(cases),tasks,unknown_predictions:unknown,promotion:'MANUAL_REVIEW_REQUIRED',trade_permission:false};
}
export function compare(baseline,candidate){if(baseline.dataset_hash!==candidate.dataset_hash)throw new Error('DATASET_MISMATCH');return {baseline_model:baseline.model_version,candidate_model:candidate.model_version,changes:Object.keys(baseline.tasks).map(task=>({task,accuracy_delta:baseline.tasks[task].accuracy===null?null:candidate.tasks[task].accuracy-baseline.tasks[task].accuracy,mae_delta:baseline.tasks[task].mean_absolute_error===null?null:candidate.tasks[task].mean_absolute_error-baseline.tasks[task].mean_absolute_error,coverage_delta:candidate.tasks[task].coverage-baseline.tasks[task].coverage})),promotion:'NEVER_AUTOMATIC'};}
