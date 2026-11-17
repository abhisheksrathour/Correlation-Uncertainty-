"""Post-review analyses; primary study remains unchanged."""
import json,time
import numpy as np,pandas as pd
from optics import ROOT,Stack
from design import fit,fit_cvar,corr,root_cov
from evaluate import simulate,summarize,METHODS
def main():
 start=time.perf_counter();sel=json.load(open(ROOT/'data/selected_designs.json'))
 model=Stack(np.linspace(450,750,61),np.arange(0,41,5));train=Stack(np.linspace(450,750,21))
 lw=np.load(ROOT/'data/training_witnesses.npz')['learned'];cv=np.load(ROOT/'data/cvar_training_errors.npy')
 rz=np.random.default_rng(2501).normal(size=(1024,8));refined=[];rows=[]
 for method in METHODS:
  C=lw if method=='learned' else corr('common') if method=='common' else None
  r=fit_cvar(train,np.array(sel[method]['d']),cv,maxiter=660) if method=='cvar' else fit(train,method,np.array(sel[method]['d']),C,maxiter=660)
  refined.append(r)
  for case in ['iid','common','block']:
   e=4*rz@root_cov(corr(case)).T
   for label,d in [('primary',sel[method]['d']),('continued',r['d'])]:
    v=simulate(model,d,e);rows.append(dict(method=method,case=case,design=label,**summarize(v)))
  print('continuation',method,r['success'],r['nit'],flush=True)
 json.dump(refined,open(ROOT/'data/continued_designs.json','w'),indent=2)
 pd.DataFrame(rows).to_csv(ROOT/'data/continuation_audit.csv',index=False)
 rng=np.random.default_rng(2502);z=rng.standard_t(5,size=(2048,8))*np.sqrt(3/5);rows=[]
 for case in ['iid','common']:
  e=4*z@root_cov(corr(case)).T
  for method in ['learned','envelope','cvar']:
   v=simulate(model,sel[method]['d'],e);rows.append(dict(method=method,case=case,**summarize(v)))
   np.savez_compressed(ROOT/f'data/heavytail_{method}_{case}.npz',errors=e,**v)
  print('heavy tail',case,flush=True)
 pd.DataFrame(rows).to_csv(ROOT/'data/heavy_tail_audit.csv',index=False)
 z=np.random.default_rng(2503).normal(size=(512,8));rows=[]
 for bias in [-4,-2,0,2,4]:
  e=bias+2*z
  for method in METHODS:
   v=simulate(model,sel[method]['d'],e);rows.append(dict(method=method,bias_nm=bias,**summarize(v)))
   np.savez_compressed(ROOT/f'data/bias_{method}_{bias}.npz',errors=e,**v)
  print('bias',bias,flush=True)
 pd.DataFrame(rows).to_csv(ROOT/'data/bias_sweep.csv',index=False)
 json.dump(dict(elapsed_seconds=time.perf_counter()-start,role='post-review exploratory'),open(ROOT/'data/exploratory_manifest.json','w'),indent=2)
if __name__=='__main__':main()
