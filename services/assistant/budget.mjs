import {existsSync,readFileSync,writeFileSync,renameSync,mkdirSync} from 'node:fs';
import path from 'node:path';
export class Budget{
 constructor(directory,config){this.directory=directory;this.config=config;mkdirSync(directory,{recursive:true,mode:0o700});this.file=path.join(directory,'budget.json');this.state=existsSync(this.file)?JSON.parse(readFileSync(this.file,'utf8')):{day:'',requests:0,reserved_microusd:0};}
 reserve(){const c=this.config;for(const key of ['max_requests_per_day','max_daily_microusd','reserve_per_request_microusd'])if(!Number.isSafeInteger(c[key])||c[key]<=0)throw new Error('COST_BUDGET_NOT_CONFIGURED');
  const day=new Date().toISOString().slice(0,10);if(this.state.day!==day)this.state={day,requests:0,reserved_microusd:0};
  if(this.state.requests>=c.max_requests_per_day||this.state.reserved_microusd+c.reserve_per_request_microusd>c.max_daily_microusd)throw new Error('DAILY_BUDGET_EXHAUSTED');
  this.state.requests++;this.state.reserved_microusd+=c.reserve_per_request_microusd;this.save();return {reserved_microusd:c.reserve_per_request_microusd,day,requests:this.state.requests};}
 save(){const temp=this.file+'.tmp';writeFileSync(temp,JSON.stringify(this.state),{mode:0o600});renameSync(temp,this.file);}
}
