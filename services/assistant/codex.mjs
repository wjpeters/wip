import {spawn} from 'node:child_process';
import {readFileSync} from 'node:fs';
import Ajv from 'ajv';
import {TOOLS,INSTRUCTIONS,OUTPUT_SCHEMA,toolResult,validateEvidence,abstain,hash} from './policy.mjs';
const ajv=new Ajv({strict:false,allErrors:true,allowUnionTypes:true});
for(const name of ['uint','uint32','uint64'])ajv.addFormat(name,{type:'number',validate:n=>Number.isSafeInteger(n)&&n>=0});
const schemas=new Map();
for(const name of ['InitializeParams','ThreadStartParams','TurnStartParams','TurnInterruptParams','ThreadResumeParams','DynamicToolCallParams','DynamicToolCallResponse','LoginAccountParams','GetAccountParams'])schemas.set(name,ajv.compile(JSON.parse(readFileSync(new URL('./protocol/'+name+'.json',import.meta.url),'utf8'))));
const validateOutput=ajv.compile(OUTPUT_SCHEMA);
const methods={'initialize':'InitializeParams','account/login/start':'LoginAccountParams','account/read':'GetAccountParams','thread/start':'ThreadStartParams','thread/resume':'ThreadResumeParams','turn/start':'TurnStartParams','turn/interrupt':'TurnInterruptParams'};
export const LOCKED_CONFIG={'features.shell_tool':false,'features.unified_exec':false,'features.apply_patch_freeform':false,'features.apps':false,'features.multi_agent':false,'web_search':'disabled','mcp_servers':{},'shell_environment_policy.inherit':'none','analytics.enabled':false,'check_for_update_on_startup':false};
export class CodexBridge{
 constructor({command='codex',args=[],spawnFn=spawn,cwd='/app/empty',timeoutMs=60000}={}){this.command=command;this.args=args;this.spawnFn=spawnFn;this.cwd=cwd;this.timeoutMs=timeoutMs;this.pending=new Map();this.seq=0;this.thread=null;this.turn=null;this.context={};this.output='';this.events=()=>{};this.finish=null;this.active=false;this.usage=null;this.frame='';}
 async start(){
  if(this.child)return;
  const flags=Object.entries(LOCKED_CONFIG).flatMap(([k,v])=>['-c',k+'='+JSON.stringify(v)]);
  this.child=this.spawnFn(this.command,[...this.args,'app-server',...flags],{cwd:this.cwd,env:{PATH:process.env.PATH,HOME:'/home/node',CODEX_HOME:'/home/node/.codex',LANG:'C.UTF-8'},stdio:['pipe','pipe','pipe']});
  this.child.stdout.on('data',chunk=>{this.frame+=chunk.toString();if(this.frame.length>1048576)return this.fail('PROTOCOL_FRAME_LIMIT');let pos;while((pos=this.frame.indexOf('\n'))>=0){const line=this.frame.slice(0,pos);this.frame=this.frame.slice(pos+1);if(line.trim())try{this.handle(JSON.parse(line))}catch{this.fail('INVALID_PROTOCOL_MESSAGE')}}});
  this.child.stderr.on('data',()=>{}); // Never print potentially secret-bearing provider diagnostics.
  this.child.on('error',()=>this.fail('CODEX_PROCESS_UNAVAILABLE'));this.child.on('exit',()=>this.fail('CODEX_PROCESS_EXITED'));
  await this.rpc('initialize',{clientInfo:{name:'modern_trade_terminal',version:'0.5.0'},capabilities:{experimentalApi:true}});this.send({method:'initialized'});
 }
 send(message){if(!this.child?.stdin.writable)throw new Error('CODEX_NOT_RUNNING');this.child.stdin.write(JSON.stringify(message)+'\n');}
 rpc(method,params){if(!methods[method]||!schemas.get(methods[method])(params))return Promise.reject(new Error('PROTOCOL_OR_METHOD_DENIED'));
  const id=++this.seq;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(new Error('PROTOCOL_TIMEOUT'))},10000);this.pending.set(id,{resolve,reject,timer});this.send({id,method,params})});}
 fail(reason){for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(new Error(reason))}this.pending.clear();if(this.finish){this.finish.reject(new Error(reason));this.finish=null}this.active=false;if(this.child){const child=this.child;this.child=null;child.kill('SIGKILL')}}
 handle(message){
  if(message.id!==undefined&&message.method===undefined){const pending=this.pending.get(message.id);if(!pending)return;clearTimeout(pending.timer);this.pending.delete(message.id);if(message.error)pending.reject(new Error('CODEX_RPC_ERROR'));else pending.resolve(message.result);return;}
  const p=message.params||{};
  if(message.method==='turn/started'&&p.threadId===this.thread&&this.finish&&p.turn?.id)this.turn=p.turn.id;
  if(message.id!==undefined){
   if(message.method==='item/tool/call'){
    if(!schemas.get('DynamicToolCallParams')(p)||p.threadId!==this.thread||p.turnId!==this.turn)return this.fail('TOOL_SESSION_MISMATCH');
    let result;try{result=toolResult(p.tool,p.arguments,this.context)}catch{result={contentItems:[{type:'inputText',text:'TOOL_DENIED'}],success:false}}
    if(!schemas.get('DynamicToolCallResponse')(result))return this.fail('TOOL_RESPONSE_SCHEMA');
    this.send({id:message.id,result});this.events({type:'tool',name:TOOLS.some(t=>t.name===p.tool)?p.tool:'DENIED',success:result.success});return;
   }
   // No approvals, shell, file changes, elicitation, auth refresh or mutable API are delegated.
   this.send({id:message.id,error:{code:-32601,message:'CAPABILITY_DENIED'}});this.fail('UNAUTHORIZED_SERVER_REQUEST');return;
  }
  if(p.threadId&&this.thread&&p.threadId!==this.thread)return;
  if(message.method==='item/agentMessage/delta'){
   if(p.turnId&&this.turn&&p.turnId!==this.turn)return;
   if(typeof p.delta!=='string')return this.fail('INVALID_TEXT_DELTA');this.output+=p.delta;
   if(this.output.length>24000)return this.fail('OUTPUT_LIMIT');this.events({type:'delta',text:p.delta,unverified:true});
  }
  if(message.method==='thread/tokenUsage/updated'){this.usage=p.tokenUsage;const total=p.tokenUsage?.last?.totalTokens??p.tokenUsage?.total?.totalTokens;if(typeof total==='number'&&total>16000)this.fail('TOKEN_CAP_REACHED');}
  if(message.method==='item/started'&&p.item&&!['userMessage','agentMessage','reasoning','dynamicToolCall','plan'].includes(p.item.type))this.fail('UNEXPECTED_TOOL_ITEM');
  if(message.method==='item/completed'&&p.item?.type==='agentMessage'&&typeof p.item.text==='string'){this.output=p.item.text;if(this.output.length>24000)this.fail('OUTPUT_LIMIT');}
  if(message.method==='turn/completed'&&this.finish){const finish=this.finish;this.finish=null;this.active=false;if(p.turn?.status!=='completed')finish.reject(new Error('TURN_'+String(p.turn?.status||'UNKNOWN')));else finish.resolve(this.output);}
 }
 async analyze(request,config,{onEvent=()=>{},threadId=null,signal}={}){
  if(this.active)return abstain('BUSY');
  if(!config.codex_key||!config.codex_model||/latest$/i.test(config.codex_model))return abstain('NOT_RUN_MISSING_CREDENTIALS_OR_PINNED_MODEL');
  this.active=true;this.events=onEvent;this.context=request.context;this.output='';this.usage=null;
  const timer=setTimeout(()=>this.fail('DEADLINE_EXCEEDED'),this.timeoutMs);const abort=()=>this.fail('CANCELED');signal?.addEventListener('abort',abort,{once:true});
  try{
   await this.start();await this.rpc('account/login/start',{type:'apiKey',apiKey:config.codex_key});const auth=await this.rpc('account/read',{refreshToken:false});if(!auth.account)throw new Error('AUTH_REQUIRED');
   const base={model:config.codex_model,cwd:this.cwd,sandbox:'read-only',approvalPolicy:'never',config:LOCKED_CONFIG,developerInstructions:INSTRUCTIONS,runtimeWorkspaceRoots:[]};
   const thread=threadId?await this.rpc('thread/resume',{...base,threadId}):await this.rpc('thread/start',{...base,environments:[],ephemeral:false,dynamicTools:TOOLS});
   if(!thread.thread?.id)throw new Error('THREAD_ID_MISSING');if(thread.model!==config.codex_model)throw new Error('MODEL_VERSION_CHANGED');if(thread.approvalPolicy!=='never'||thread.sandbox?.type!=='readOnly')throw new Error('PERMISSIONS_NOT_ENFORCED');this.thread=thread.thread.id;
   const completion=new Promise((resolve,reject)=>{this.finish={resolve,reject}});completion.catch(()=>{});
   const started=await this.rpc('turn/start',{threadId:this.thread,environments:[],input:[{type:'text',text:JSON.stringify({question:request.prompt,untrusted_evidence:request.context})}],outputSchema:OUTPUT_SCHEMA});
   this.turn=started.turn?.id;if(!this.turn)throw new Error('TURN_ID_MISSING');
   const text=await completion;let output;try{output=JSON.parse(text)}catch{throw new Error('INVALID_STRUCTURED_OUTPUT')}
   if(!validateOutput(output))throw new Error('OUTPUT_SCHEMA_MISMATCH');
   return {schema_version:1,disposition:'REVIEW',model_version:config.codex_model,protocol_version:'0.141.0',thread_id:this.thread,input_hash:hash(request.context),output:validateEvidence(output,request.context),usage:this.usage,execution_authorized:false};
  }catch(e){return abstain(e.message,{protocol_version:'0.141.0'});}finally{clearTimeout(timer);signal?.removeEventListener('abort',abort);this.active=false;this.finish=null;this.fail('SESSION_CLOSED');}
 }
}
