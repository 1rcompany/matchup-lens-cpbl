"""Rebuild the historical Matchup Lens demo; Python 3 + numpy only."""
from __future__ import annotations
import argparse, collections, csv, hashlib, json, math, pathlib, urllib.request, zipfile
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = {
    2024: ('v0.1.0-2024', 'CPBL-2024-OpenData.zip', '1711009c9d3bac68ca13b2b68f409587fdce2deea3c9fbb5ad68131fccb1d19f'),
    2025: ('v0.1.0-2025', 'CPBL-2025-OpenData.zip', 'eb84d824e0fdce032a47aebcad5d2f64610629adbb806dd23d7e282eb6d390f6'),
}
VALID = {'1B','2B','3B','HR','IHR','SO','uBB','HBP','GO','FO','FC','E','SH','SF','GIDP','DP','TP','SH_FC','SH_E','SF_E','GIDP_E'}

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',',':')), encoding='utf-8')

def read_data(raw):
    rows, players, audit = [], {'b':{},'p':{}}, {}
    for year, (tag, filename, expected) in ASSETS.items():
        path = raw / filename
        if not path.exists():
            raw.mkdir(parents=True,exist_ok=True)
            url = f'https://github.com/rebas-tw/rebas.tw-open-data/releases/download/{tag}/{filename}'
            with urllib.request.urlopen(url,timeout=60) as src, path.open('wb') as out:
                while chunk := src.read(1024*1024): out.write(chunk)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'Source SHA-256 mismatch'
        a = collections.Counter(); games=set(); excluded=collections.Counter(); dates=[]
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist()):
                if not name.endswith('.json') or name.endswith('OpenData.json'): continue
                g = json.loads(z.read(name)); gid=f'{year}-G{g["seq"]}'
                assert gid not in games, 'Duplicate game'
                games.add(gid); dates.append(g['date'][:10])
                for side, other in [('away','home'),('home','away')]:
                    maps={}
                    for role, box in [('b',side+'BatterBox'),('p',other+'PitcherBox')]:
                        maps[role]={}
                        for pl in g[box]:
                            nm=pl['playerName']; pid=pl['playerId']
                            if nm in maps[role]: assert maps[role][nm]==pid, 'Ambiguous same-game name'
                            maps[role][nm]=pid
                            team=g[(side if role=='b' else other)+'Team']
                            old=players[role].get(pid)
                            if old is None or g['date']>old['date']:
                                players[role][pid]={'id':pid,'name':nm,'team':team,'date':g['date']}
                    for pa in g[side+'PAList']:
                        a['all_records']+=1
                        result=pa.get('result',pa.get('results',''))
                        if result not in VALID:
                            excluded[result or 'empty']+=1;continue
                        b=maps['b'].get(pa.get('batterName')); p=maps['p'].get(pa.get('pitcherName'))
                        if not b or not p:
                            excluded['unresolved_player_id']+=1;continue
                        rows.append({'year':year,'date':g['date'][:10],'game':gid,'b':b,'p':p,'y':int(result=='SO'),'result':result})
                        a['eligible_pa']+=1;a['strikeouts']+=int(result=='SO')
        audit[str(year)]={**dict(a),'games':len(games),'start':min(dates),'end':max(dates),'excluded':dict(excluded),'sha256':expected}
    rows.sort(key=lambda r:(r['date'],r['game']))
    return rows,players,audit

class Counts:
    def __init__(self, rows):
        self.n=len(rows);self.k=sum(r['y'] for r in rows);self.q=self.k/self.n
        self.b=collections.defaultdict(lambda:[0,0]);self.p=collections.defaultdict(lambda:[0,0]);self.pair=collections.defaultdict(lambda:[0,0])
        for r in rows:
            for m,key in [(self.b,r['b']),(self.p,r['p']),(self.pair,(r['b'],r['p']))]:
                m[key][0]+=1;m[key][1]+=r['y']
    def features(self,b,p,strength):
        n,k=self.pair.get((b,p),(0,0));bn,bk=self.b.get(b,(0,0));pn,pk=self.p.get(p,(0,0))
        # Exclude this pair from both player margins so pair counts do not enter the prior twice.
        qb=(bk-k+strength*self.q)/(bn-n+strength)
        qp=(pk-k+strength*self.q)/(pn-n+strength)
        logit=lambda x: math.log(x/(1-x))
        v=logit(qb)+logit(qp)-logit(self.q)
        base=1/(1+math.exp(-v))
        return n,k,base
    def predict(self, rows, strength, m):
        ans=[]
        cache={}
        for r in rows:
            key=(r['b'],r['p'])
            if key not in cache:
                n,k,p0=self.features(*key,strength)
                cache[key]=(self.q,(k+.5)/(n+1) if n else self.q,(k+20*self.q)/(n+20),p0,(k+m*p0)/(n+m))
            ans.append(cache[key])
        return np.array(ans)

def losses(y,p):
    p=np.clip(p,1e-8,1-1e-8)
    return (p-y[:,None])**2, -(y[:,None]*np.log(p)+(1-y[:,None])*np.log1p(-p))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--raw-dir',type=pathlib.Path,default=ROOT/'data'/'raw');args=parser.parse_args()
    rows,players,audit=read_data(args.raw_dir)
    train=[r for r in rows if r['year']==2024 and r['date']<'2024-08-01']
    val=[r for r in rows if r['year']==2024 and r['date']>='2024-08-01']
    test=[r for r in rows if r['year']==2025]
    c=Counts(train);vy=np.array([r['y'] for r in val]);grid=[]
    for strength in [30,100,300]:
        for m in [10,25,50,100,200,500,1000]:
            pred=c.predict(val,strength,m);br,ll=losses(vy,pred)
            grid.append({'strength':strength,'m':m,'log_loss':float(ll[:,4].mean()),'brier':float(br[:,4].mean())})
    best=min(grid,key=lambda x:(x['log_loss'],x['strength'],x['m']))
    ref=[r for r in rows if r['year']==2024];c=Counts(ref)
    pred=c.predict(test,best['strength'],best['m']);y=np.array([r['y'] for r in test]);br,ll=losses(y,pred)
    names=['league','raw_jeffreys','league_shrink','player_context','matchup_shrink']
    metrics={name:{'brier':float(br[:,i].mean()),'log_loss':float(ll[:,i].mean())} for i,name in enumerate(names)}
    group=collections.defaultdict(list)
    for i,r in enumerate(test): group[r['game']].append(i)
    ids=[np.array(v) for v in group.values()];sizes=np.array([len(v) for v in ids]);sums=np.array([br[v].sum(axis=0) for v in ids])
    rng=np.random.default_rng(20261104);draw=rng.integers(0,len(ids),(2000,len(ids)))
    boots=sums[draw].sum(axis=1)/sizes[draw].sum(axis=1)[:,None]
    deltas={}
    for i,name in enumerate(names[:-1]):
        d=boots[:,4]-boots[:,i]
        deltas[name]={'delta_brier':float((br[:,4]-br[:,i]).mean()),'ci95':[float(x) for x in np.quantile(d,[.025,.975])]}
    n_by_pair=collections.Counter((r['b'],r['p']) for r in ref)
    sparse={}
    for name,lo,hi in [('unseen',0,0),('1_5',1,5),('6_15',6,15),('16_plus',16,100000)]:
        indices=np.array([i for i,r in enumerate(test) if lo<=n_by_pair[(r['b'],r['p'])]<=hi],dtype=int)
        sparse[name]={'pa':len(indices),'brier':{n:float(br[indices,i].mean()) for i,n in enumerate(names)}}
    ct=Counts(test);pairs={}
    for b,p in set(c.pair)|set(ct.pair):
        n,k,p0=c.features(b,p,best['strength']);tn,tk=ct.pair.get((b,p),(0,0))
        pairs[b+'|'+p]=[n,k,round(p0,8),tn,tk]
    bdict={x:{**v,'n':c.b.get(x,[0,0])[0],'k':c.b.get(x,[0,0])[1]} for x,v in players['b'].items()}
    pdict={x:{**v,'n':c.p.get(x,[0,0])[0],'k':c.p.get(x,[0,0])[1]} for x,v in players['p'].items()}
    # Deterministic high-contrast examples with a subsequent-season observation.
    examples=[]
    for key,(n,k,p0,tn,tk) in pairs.items():
        if 3<=n<=10 and tn>=3:
            adjusted=(k+best['m']*p0)/(n+best['m'])
            examples.append((abs(k/n-adjusted),key))
    examples=[key for _,key in sorted(examples,reverse=True)[:3]]
    summary={'generated':'2026-11-04','snapshot':'2025-01-01','reference_year':2024,'test_year':2025,'audit':audit,'train_pa':len(train),'validation_pa':len(val),'test_pa':len(test),'validation_start':'2024-08-01','parameters':best,'grid':grid,'league_k_rate':c.q,'metrics':metrics,'delta_brier':deltas,'bootstrap_games':len(ids),'bootstrap_repetitions':2000,'sparse_test':sparse,'reference_pairs':len(c.pair),'examples':examples}
    data={'summary':summary,'batters':bdict,'pitchers':pdict,'pairs':pairs}
    dump(ROOT/'dist'/'data.json',data);dump(ROOT/'analysis'/'results.json',summary)
    with (ROOT/'analysis'/'eligible_pa.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['year','date','game','b','p','y','result']);w.writeheader();w.writerows(rows)
    assert len(set(r['game'] for r in ref))==360 and len(group)==360
    assert max(r['date'] for r in ref)<min(r['date'] for r in test)
    assert all(0<x<1 for x in pred.ravel())
    assert sum(audit[str(y)]['eligible_pa'] for y in [2024,2025])==len(rows)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['grid']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
