import {useEffect,useRef} from 'react';
import {createChart,CandlestickSeries,HistogramSeries,LineSeries,AreaSeries,PriceScaleMode,ColorType,type UTCTimestamp} from 'lightweight-charts';
import type {History} from '../types';
export default function MarketChart({history,theme,sma,style='candles',log=false,indicator='none',level=''}:{history:History;theme:string;sma:boolean;style?:string;log?:boolean;indicator?:string;level?:string}) {
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!ref.current)return;
  const light=theme==='light';const positive=light?'#17674e':'#62d4ad',negative=light?'#ae2942':'#ff8c99';
  const chart=createChart(ref.current,{autoSize:true,layout:{background:{type:ColorType.Solid,color:light?'#ffffff':'#0b0f16'},textColor:light?'#53647a':'#939fb3',fontSize:12,attributionLogo:true},grid:{vertLines:{color:light?'#edf1f7':'#182130'},horzLines:{color:light?'#edf1f7':'#182130'}},timeScale:{timeVisible:true,borderVisible:false},rightPriceScale:{mode:log?PriceScaleMode.Logarithmic:PriceScaleMode.Normal,borderVisible:false,scaleMargins:{top:.1,bottom:.26}},localization:{locale:'nl-NL',priceFormatter:(price:number)=>new Intl.NumberFormat('nl-NL',{minimumFractionDigits:2,maximumFractionDigits:2}).format(price)}});
  const priceSeries=style==='candles'?chart.addSeries(CandlestickSeries,{upColor:positive,downColor:negative,wickUpColor:positive,wickDownColor:negative,borderVisible:false,priceFormat:{type:'price',precision:2,minMove:.01}}):style==='area'?chart.addSeries(AreaSeries,{lineColor:positive,topColor:positive+'55',bottomColor:positive+'05'}):chart.addSeries(LineSeries,{color:positive,lineWidth:2});
  priceSeries.setData(history.rows.map(r=>style==='candles'?{time:r.time as UTCTimestamp,open:Number(r.open),high:Number(r.high),low:Number(r.low),close:Number(r.close)}:{time:r.time as UTCTimestamp,value:Number(r.close)}));
  if(Number(level)>0)priceSeries.createPriceLine({price:Number(level),color:light?'#9b6500':'#f2bc62',lineWidth:1,lineStyle:2,axisLabelVisible:true,title:'Eigen prijsniveau'});
  const volume=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceScaleId:'volume',lastValueVisible:false,priceLineVisible:false});
  volume.priceScale().applyOptions({scaleMargins:{top:.82,bottom:0}});
  volume.setData(history.rows.map(r=>({time:r.time as UTCTimestamp,value:Number(r.volume),color:Number(r.close)>=Number(r.open)?positive+'66':negative+'66'})));
  if(sma){const line=chart.addSeries(LineSeries,{color:light?'#2457b3':'#78a9ff',lineWidth:2,priceLineVisible:false,lastValueVisible:false});line.setData(history.rows.filter(r=>r.sma20!==null).map(r=>({time:r.time as UTCTimestamp,value:Number(r.sma20)})))}
  if(indicator!=='none'){
   const pane=['rsi14','atr14','macd'].includes(indicator)?1:0;
   const line=chart.addSeries(LineSeries,{color:light?'#8c4dc2':'#c99af5',lineWidth:2,priceLineVisible:false,lastValueVisible:true},pane);
   const values=history.rows.map(r=>({time:r.time as UTCTimestamp,value:r[indicator as keyof typeof r]})).filter(r=>r.value!==null&&r.value!==undefined);
   line.setData(values.map(r=>({time:r.time,value:Number(r.value)})));
   if(indicator==='macd'){const signal=chart.addSeries(LineSeries,{color:positive,lineWidth:1,priceLineVisible:false},pane);signal.setData(history.rows.filter(r=>r.macd_signal!==null&&r.macd_signal!==undefined).map(r=>({time:r.time as UTCTimestamp,value:Number(r.macd_signal)})))}
  }
  chart.timeScale().fitContent();return()=>chart.remove();
 },[history,theme,sma,style,log,indicator,level]);
 return <div ref={ref} className="market-chart" aria-label="Interactieve gesimuleerde koersgrafiek. Dezelfde gegevens staan onder Koerstabel." role="region"/>;
}
