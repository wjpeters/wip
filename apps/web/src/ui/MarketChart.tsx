import {useEffect,useRef} from 'react';
import {createChart,CandlestickSeries,HistogramSeries,LineSeries,ColorType,type UTCTimestamp} from 'lightweight-charts';
import type {History} from '../types';
export default function MarketChart({history,theme,sma}:{history:History;theme:string;sma:boolean}) {
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!ref.current)return;
  const light=theme==='light';const positive=light?'#17674e':'#62d4ad',negative=light?'#ae2942':'#ff8c99';
  const chart=createChart(ref.current,{autoSize:true,layout:{background:{type:ColorType.Solid,color:light?'#ffffff':'#0b0f16'},textColor:light?'#53647a':'#939fb3',fontSize:12,attributionLogo:true},grid:{vertLines:{color:light?'#edf1f7':'#182130'},horzLines:{color:light?'#edf1f7':'#182130'}},timeScale:{timeVisible:true,borderVisible:false},rightPriceScale:{borderVisible:false,scaleMargins:{top:.1,bottom:.26}},localization:{locale:'nl-NL',priceFormatter:(price:number)=>new Intl.NumberFormat('nl-NL',{minimumFractionDigits:2,maximumFractionDigits:2}).format(price)}});
  const candles=chart.addSeries(CandlestickSeries,{upColor:positive,downColor:negative,wickUpColor:positive,wickDownColor:negative,borderVisible:false,priceFormat:{type:'price',precision:2,minMove:.01}});
  candles.setData(history.rows.map(r=>({time:r.time as UTCTimestamp,open:Number(r.open),high:Number(r.high),low:Number(r.low),close:Number(r.close)})));
  const volume=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceScaleId:'volume',lastValueVisible:false,priceLineVisible:false});
  volume.priceScale().applyOptions({scaleMargins:{top:.82,bottom:0}});
  volume.setData(history.rows.map(r=>({time:r.time as UTCTimestamp,value:Number(r.volume),color:Number(r.close)>=Number(r.open)?positive+'66':negative+'66'})));
  if(sma){const line=chart.addSeries(LineSeries,{color:light?'#2457b3':'#78a9ff',lineWidth:2,priceLineVisible:false,lastValueVisible:false});line.setData(history.rows.filter(r=>r.sma20!==null).map(r=>({time:r.time as UTCTimestamp,value:Number(r.sma20)})))}
  chart.timeScale().fitContent();return()=>chart.remove();
 },[history,theme,sma]);
 return <div ref={ref} className="market-chart" aria-label="Interactieve gesimuleerde koersgrafiek. Dezelfde gegevens staan onder Koerstabel." role="region"/>;
}
