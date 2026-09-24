import http from 'node:http';
import {readFileSync,existsSync,writeFileSync,renameSync,mkdirSync} from 'node:fs';
import {timingSafeEqual} from 'node:crypto';
import {CodexBridge} from './codex.mjs';
import {assess} from './jev.mjs';
import {validateRequest,abstain,hash} from './policy.mjs';
import {Budget} from './budget.mjs';
process.umask(0o077);
const configFile=process.env.MTT_AI_CONFIG||'/run/secrets/ai_config';
const config=existsSync(configFile)?JSON.parse(readFileSync(configFile,'utf8')):{enabled:false};
const tokenFile=process.env.MTT_BRIDGE_TOKEN||'/run/secrets/assistant_token';
const secret=existsSync(tokenFile)?readFileSync(tokenFile,'utf8').trim():'';
const stateDir=process.env.MTT_AI_STATE||'/home/node/.codex/mtt-state';mkdirSync(stateDir,{recursive:true,mode:0o700});
const budget=new Budget(stateDir,config),sessionsFile=stateDir+'/sessions.json';let sessions=existsSync(sessionsFile)?JSON.parse(readFileSync(sessionsFile,'utf8')):{};
let active=false;
function authorized(req){const token=(req.headers.authorization||'').replace(/^Bearer /,'');return secret.length>=32&&Buffer.byteLength(token)===Buffer.byteLength(secret)&&timingSafeEqual(Buffer.from(token),Buffer.from(secret));}
function json(res,status,value){res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(value));}
http.createServer(async(req,res)=>{
 if(req.url==='/health'&&req.method==='GET')return json(res,200,{status:'ok',mode:config.enabled?'CONFIGURED_OPT_IN':'DISABLED',protocol:'0.141.0'});
 if(!authorized(req))return json(res,403,{detail:'BRIDGE_AUTH_REQUIRED'});
 if(req.url==='/status'&&req.method==='GET')return json(res,200,{enabled:config.enabled===true,codex_configured:!!config.codex_key&&!!config.codex_model,jev_configured:!!config.jev_key&&!!config.jev_model,protocol_version:'0.141.0',privacy:'PUBLIC_DATA_AI_ONLY',budget:{max_requests_per_day:config.max_requests_per_day||0,max_daily_microusd:config.max_daily_microusd||0,reserve_per_request_microusd:config.reserve_per_request_microusd||0,used:budget.state},verification:'NOT_RUN_MISSING_CREDENTIALS_UNTIL_FIRST_VERIFIED_CALL'});
 if(req.url!=='/analyze'||req.method!=='POST')return json(res,404,{detail:'ROUTE_DENIED'});
 if(active)return json(res,429,abstain('ONE_ANALYSIS_AT_A_TIME'));
 if(config.enabled!==true)return json(res,200,abstain('CLOUD_DISABLED'));
 let size=0,chunks=[];
 try{for await(const chunk of req){size+=chunk.length;if(size>40000)return json(res,413,abstain('REQUEST_LIMIT'));chunks.push(chunk)}
  const request=validateRequest(JSON.parse(Buffer.concat(chunks).toString()));
  if(request.provider==='CODEX'&&!config.codex_key||request.provider==='JEV'&&!config.jev_key)return json(res,200,abstain('NOT_RUN_MISSING_CREDENTIALS'));
  if(active)return json(res,429,abstain('ONE_ANALYSIS_AT_A_TIME'));
  active=true;const reservation=budget.reserve();res.writeHead(200,{'Content-Type':'application/x-ndjson','Cache-Control':'no-store','X-Accel-Buffering':'no'});
  const controller=new AbortController();res.on('close',()=>{if(!res.writableEnded)controller.abort()});const timer=setTimeout(()=>controller.abort(),65000);
  const emit=event=>{if(!res.destroyed)res.write(JSON.stringify(event)+'\n')};emit({type:'started',provider:request.provider,input_hash:hash(request.context),reservation});
  try{
   const key=request.conversation_id;const previous=sessions[key];
   if(previous&&(previous.context_hash!==hash(request.context)||previous.model!==config.codex_model))delete sessions[key];
   const result=request.provider==='JEV'?await assess(request,config,{signal:controller.signal}):await new CodexBridge().analyze(request,config,{onEvent:emit,threadId:sessions[key]?.thread_id,signal:controller.signal});
   if(result.thread_id){sessions[key]={thread_id:result.thread_id,context_hash:hash(request.context),model:config.codex_model};if(Object.keys(sessions).length>500)sessions=Object.fromEntries(Object.entries(sessions).slice(-500));writeFileSync(sessionsFile+'.tmp',JSON.stringify(sessions),{mode:0o600});renameSync(sessionsFile+'.tmp',sessionsFile)}
   emit({type:'result',result:{...result,budget_reservation:reservation,cost_note:'Local reservation is a conservative accounting budget, not a provider billing cap. Set an independent provider spending limit.'}});res.end();
  }finally{clearTimeout(timer);active=false;}
 }catch(e){active=false;if(!res.headersSent)json(res,422,abstain(e.message));else res.end(JSON.stringify({type:'result',result:abstain('BRIDGE_FAILURE')})+'\n');}
}).listen(8090,'0.0.0.0');
