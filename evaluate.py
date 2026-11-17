"""Independent nonlinear test audit. All quantities are numerical simulations."""
import json,time
import numpy as np,pandas as pd
from scipy.stats import norm
from optics import ROOT,Stack
from design import corr,root_cov,Objective

METHODS=['nominal','iid','common','learned','envelope','cvar']
CASES=['iid','common','alternating','ar0.6','ar-0.6','block','random','sign']
def wilson(k,n):
 z=norm.ppf(.975);p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den
 h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return c-h,c+h
def simulate(model,d,errors,batch=24):
 d=np.asarray(d);valid=np.all(d+errors>0,axis=1);out=model.evaluate(d,jac=True)
 linear=out['R'][None,:]+errors@out['J'].T
 lm=linear.max(axis=1);R=[];A=[];T=[]
 for i in range(0,len(errors),batch):
  v=model.evaluate(d+errors[i:i+batch],transmission=True)
  R.extend(v['R'].max(axis=1));A.extend(v['A'].max(axis=1));T.extend(v['T'].min(axis=1))
 R=np.asarray(R);A=np.asarray(A);T=np.asarray(T);R[~valid]=np.inf;A[~valid]=np.nan;T[~valid]=np.nan
 return dict(maxR=R,maxA=A,minT=T,linear=lm,valid=valid)
def summarize(v):
 r=v['maxR'];n=len(r);k=int(np.sum(r<=.05));lo,hi=wilson(k,n)
 return dict(n=n,yield_rate=k/n,yield_low=lo,yield_high=hi,q95=np.quantile(r,.95),q99=np.quantile(r,.99),
  cvar95=np.sort(r)[-int(np.ceil(.05*n)):].mean(),maximum_R=r.max(),maxA=np.nanmax(v['maxA']),minT=np.nanmin(v['minT']),
  linear_q95=np.quantile(v['linear'],.95),mean_remainder=(r-v['linear']).mean(),
  exceed_linear_fraction=np.mean(r>v['linear']),invalid=int(np.sum(~v['valid'])))
def cases():
 cs={k:corr(k) for k in CASES if k not in ['random','sign']}
 a=np.random.default_rng(2202).normal(size=(8,8));a=a@a.T+.2*np.eye(8);s=np.sqrt(np.diag(a));cs['random']=a/s[:,None]/s[None,:]
 return cs
def main():
 t=time.perf_counter();sel=json.load(open(ROOT/'data/selected_designs.json'));model=Stack(np.linspace(450,750,61),np.arange(0,41,5))
 cs=cases();np.savez(ROOT/'data/process_covariances.npz',**cs)
 z=np.random.default_rng(2201).normal(size=(4096,8));np.save(ROOT/'data/test_standard_normals.npy',z)
 designmodel=Stack(np.linspace(450,750,21));rows=[];raw={};nominal=[]
 for method in METHODS:
  d=np.asarray(sel[method]['d']);v=model.evaluate(d,transmission=True)
  nominal.append(dict(method=method,maxR=v['R'].max(),maxA=v['A'].max(),minT=v['T'].min(),
   objective=sel[method]['objective'],start=sel[method]['start'],seconds=sel[method]['seconds']))
  for case in CASES:
   if case=='sign':
    o=designmodel.evaluate(d,jac=True);j=np.argmax(o['R']+Objective(designmodel).z*4*np.abs(o['J']).sum(axis=1))
    direction=np.sign(o['J'][j]);direction[direction==0]=1;C=np.outer(direction,direction)
    np.save(ROOT/f'data/sign_covariance_{method}.npy',C)
   else:C=cs[case]
   errors=4*z@root_cov(C).T;v=simulate(model,d,errors)
   row=dict(method=method,case=case,**summarize(v));rows.append(row);raw[(method,case)]=v['maxR']
   np.savez_compressed(ROOT/f'data/test_{method}_{case}.npz',errors=errors,**v)
   print(method,case,'yield',round(row['yield_rate'],4),'q95',round(row['q95'],4),flush=True)
  pd.DataFrame(rows).to_csv(ROOT/'data/primary_metrics.csv',index=False)
 pd.DataFrame(nominal).to_csv(ROOT/'data/nominal_metrics.csv',index=False)
 contrasts=[];rng=np.random.default_rng(2210)
 for case in CASES[:-1]:
  a=raw[('envelope',case)]<=.05
  for method in METHODS:
   if method=='envelope':continue
   d=a.astype(int)-(raw[(method,case)]<=.05).astype(int)
   bs=[]
   for j in range(2000):bs.append(d[rng.integers(0,len(d),len(d))].mean())
   contrasts.append(dict(case=case,comparison=method,difference=d.mean(),low=np.quantile(bs,.025),high=np.quantile(bs,.975)))
 pd.DataFrame(contrasts).to_csv(ROOT/'data/paired_contrasts.csv',index=False)
 json.dump({'elapsed_seconds':time.perf_counter()-t,'cases':CASES,'samples_per_case':4096,'grid_points':len(model.w)},open(ROOT/'data/evaluation_manifest.json','w'),indent=2)
if __name__=='__main__':main()
