"""Frozen-2024 predictions evaluated on 2025; no tuning on the test season."""
import csv,json,pathlib,sys
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from build_data import Counts,losses
root=pathlib.Path(__file__).resolve().parents[1]
d=json.loads((root/'dist/data.json').read_text())
rows=list(csv.DictReader((root/'analysis/eligible_pa.csv').open(encoding='utf-8-sig')))
for r in rows:r['year']=int(r['year']);r['y']=int(r['y'])
ref=[r for r in rows if r['year']==2024];test=[r for r in rows if r['year']==2025]
p=Counts(ref).predict(test,d['summary']['parameters']['strength'],d['summary']['parameters']['m']);y=np.array([r['y'] for r in test]);br,ll=losses(y,p)
assert abs(br[:,4].mean()-d['summary']['metrics']['matchup_shrink']['brier'])<1e-12
out={'test_pa':len(test),'reference_year':2024,'test_year':2025,'bin_width':.05,'models':{}}
for name,col in [('player_context',3),('matchup_shrink',4)]:
 bins=[]
 for lo in np.arange(0,1,.05):
  mask=(p[:,col]>=lo)&(p[:,col]<lo+.05+1e-12)
  # Integer bin index avoids floating point boundary overlap.
  mask=np.minimum((p[:,col]*20).astype(int),19)==round(lo*20)
  if mask.any():bins.append({'lo':round(float(lo),2),'hi':round(float(lo+.05),2),'n':int(mask.sum()),'predicted':float(p[mask,col].mean()),'observed':float(y[mask].mean())})
 assert sum(b['n'] for b in bins)==len(test)
 out['models'][name]={'bins':bins,'ece':sum(b['n']*abs(b['predicted']-b['observed']) for b in bins)/len(test)}
(root/'dist/calibration.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v['ece'] for k,v in out['models'].items()}))
