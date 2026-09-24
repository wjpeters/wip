let csrf = '';
export function setCsrf(value: string) { csrf = value; }
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`/api${path}`, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', ...(body === undefined ? {} : {'X-CSRF-Token': csrf})},
    ...(body === undefined ? {} : {body: JSON.stringify(body)})});
  if (!r.ok) { const error = await r.json().catch(() => ({})); throw new Error(typeof error.detail === 'string' ? error.detail : 'Controleer de invoer. Bedragen gebruiken een punt als decimaalteken.'); }
  return r.json() as Promise<T>;
}

export async function streamApi(path:string,body:unknown,onEvent:(event:Record<string,unknown>)=>void,signal:AbortSignal){
 const r=await fetch(`/api${path}`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body),signal});
 if(!r.ok){const e=await r.json().catch(()=>({}));throw new Error(typeof e.detail==='string'?e.detail:'Analyse niet beschikbaar')}
 if(!r.body)throw new Error('Geen antwoord ontvangen');
 const reader=r.body.getReader(),decoder=new TextDecoder();let pending='';let total=0;
 while(true){const {done,value}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});total+=value.length;if(total>400000){await reader.cancel();throw new Error('Antwoord te groot')}
 const lines=pending.split('\n');pending=lines.pop()||'';for(const line of lines)if(line.trim())onEvent(JSON.parse(line));}
 if(pending.trim())onEvent(JSON.parse(pending));
}
