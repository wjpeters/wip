import {useEffect,useRef,type ReactNode} from 'react';
export const eur=(v:string|number)=>new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(Number(v));
export const num=(v:string|number)=>new Intl.NumberFormat('nl-NL',{maximumFractionDigits:8}).format(Number(v));
export const stamp=(v:string)=>new Date(v).toLocaleString('nl-NL',{timeZone:'Europe/Amsterdam',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
export function Icon({name}:{name:string}) {
 const p:Record<string,string>={terminal:'M3 4h18v16H3z M7 8l3 3-3 3m6 1h4',wealth:'M4 20h16M6 16v-4m6 4V5m6 11V9',plan:'M4 5h16v15H4zM8 3v4m8-4v4M7 11h4m2 4h4',source:'M8 8h8v8H8zM12 3v5m0 8v5M3 12h5m8 0h5',lab:'M9 3h6M10 3v7L4 20h16l-6-10V3M7 16h10',search:'M10 17a7 7 0 1 0 0-14 7 7 0 0 0 0 14zm5-2 6 6',close:'m6 6 12 12M6 18 18 6',sun:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1',refresh:'M20 7v5h-5M4 17v-5h5M5 8a8 8 0 0 1 13-3l2 3M4 16l2 3a8 8 0 0 0 13-3',arrow:'M4 12h16m-6-6 6 6-6 6',shield:'m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6',exit:'M10 4H4v16h6M9 12h12m-4-4 4 4-4 4'};
 return <svg aria-hidden="true" className="icon" viewBox="0 0 24 24"><path d={p[name]||p.terminal}/></svg>;
}
export function Badge({children,tone='warning'}:{children:ReactNode;tone?:string}){return <span className={`badge ${tone}`}>{children}</span>}
export function Empty({title,children}:{title:string;children:ReactNode}){return <div className="empty"><h3>{title}</h3><p>{children}</p></div>}
export function Table({headers,children,label}:{headers:string[];children:ReactNode;label:string}){return <div className="table-scroll" tabIndex={0} role="region" aria-label={label}><table><thead><tr>{headers.map(h=><th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div>}
export function Dialog({title,children,onClose,wide=false}:{title:string;children:ReactNode;onClose:()=>void;wide?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const previous=document.activeElement as HTMLElement|null;ref.current?.showModal();return()=>previous?.focus()},[]);
 return <dialog ref={ref} className={wide?'wide':''} aria-labelledby="dialog-title" onCancel={e=>{e.preventDefault();onClose()}} onClick={e=>{if(e.target===e.currentTarget)onClose()}}><div className="dialog-head"><h2 id="dialog-title">{title}</h2><button aria-label="Sluiten" className="icon-button" onClick={onClose}><Icon name="close"/></button></div>{children}</dialog>
}
export function PathChart({values,labels,label}:{values:string[];labels:string[];label:string}){
 const vals=values.map(Number);const lo=Math.min(...vals)*.98,hi=Math.max(...vals)*1.02;const span=hi-lo||1;
 const pts=vals.map((v,i)=>`${40+i/Math.max(1,vals.length-1)*840},${190-(v-lo)/span*155}`).join(' ');
 return <svg className="path-chart" viewBox="0 0 940 235" role="img" aria-label={label}>{[0,1,2,3].map(i=><g key={i}><line x1="40" x2="880" y1={35+i*52} y2={35+i*52}/><text x="890" y={39+i*52}>{Math.round((hi-i*span/3)/1000)}k</text></g>)}<polyline points={pts} fill="none" className="path-line"/><text x="40" y="220">{labels[0]}</text><text textAnchor="end" x="880" y="220">{labels.at(-1)}</text></svg>
}
