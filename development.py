from optics import *
from scipy.optimize import minimize,differential_evolution
from scipy.special import logsumexp
import json,time
st=time.time();g=Stack(np.linspace(450,750,21));rng=np.random.default_rng(123)
d=rng.uniform(25,160,8);out=g.evaluate(d,jac=True,transmission=True)
num=np.column_stack([(g.evaluate(d+np.eye(8)[j]*1e-4)['R']-g.evaluate(d-np.eye(8)[j]*1e-4)['R'])/2e-4 for j in range(8)])
r,t=g.recursive(d)
checks=dict(jacobian_max_abs=float(np.max(abs(num-out['J']))),recursive_R_error=float(np.max(abs(r-out['R']))),recursive_T_error=float(np.max(abs(t-out['T']))),minimum_absorption=float(out['A'].min()),maximum_absorption=float(out['A'].max()))
assert checks['jacobian_max_abs']<1e-7 and checks['recursive_R_error']<1e-10 and checks['recursive_T_error']<1e-10
tau=.0003
def fun(d):
 o=g.evaluate(d,jac=True);rr=o['R'];J=o['J'];e=np.exp((rr-rr.max())/tau);return float(rr.max()+tau*np.log(e.sum())),e@J/e.sum()
ans=minimize(fun,np.full(8,70.),jac=True,bounds=[(25,160)]*8,method='L-BFGS-B',options=dict(maxiter=200,ftol=1e-12,gtol=1e-7))
de=differential_evolution(lambda x:fun(x)[0],[(25,160)]*8,seed=124,popsize=7,maxiter=70,polish=False)
aa=minimize(fun,de.x,jac=True,bounds=[(25,160)]*8,method='L-BFGS-B',options=dict(maxiter=200,ftol=1e-12,gtol=1e-7))
for label,a in [('local',ans),('global_start',aa)]:
 d=a.x;out=g.evaluate(d,jac=True,transmission=True);print(label,d,'maximum R',out['R'].max(),'max A',out['A'].max(),'Tmin',out['T'].min(),flush=True)
 np.save(ROOT/'data'/f'development_{label}.npy',d)
checks.update(elapsed_seconds=time.time()-st,scope='Development only; no primary performance claim',candidate_nominal_max_R=float(g.evaluate(aa.x)['R'].max()))
(ROOT/'data/development_checks.json').write_text(json.dumps(checks,indent=2));print(checks,flush=True)
