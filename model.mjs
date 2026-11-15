export function wilson(k,n,z=1.6448536269514722){
  if(!n)return null;
  const p=k/n,zz=z*z,d=1+zz/n,c=(p+zz/(2*n))/d;
  const h=z*Math.sqrt(p*(1-p)/n+zz/(4*n*n))/d;
  return [Math.max(0,c-h),Math.min(1,c+h)];
}
export function context(b,p,league,strength){
  const qb=(b.k+strength*league)/(b.n+strength);
  const qp=(p.k+strength*league)/(p.n+strength);
  const logit=x=>Math.log(x/(1-x));
  return 1/(1+Math.exp(-(logit(qb)+logit(qp)-logit(league))));
}
export function inspect(data,bid,pid){
  const s=data.summary,b=data.batters[bid],p=data.pitchers[pid];
  if(!b||!p)throw new Error('Unknown player');
  const rec=data.pairs[bid+'|'+pid]||[0,0,context(b,p,s.league_k_rate,s.parameters.strength),0,0];
  const [n,k,p0,tn,tk]=rec,m=s.parameters.m;
  return {b,p,n,k,p0,tn,tk,raw:n?k/n:null,estimate:(k+m*p0)/(n+m),weight:n/(n+m),interval:wilson(k,n)};
}
