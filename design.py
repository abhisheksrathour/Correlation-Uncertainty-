"""Matched local optimizers for nominal and covariance-aware optical design."""
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from scipy.stats import norm
from sklearn.covariance import LedoitWolf
from optics import Stack,LAYERS

def corr(kind,n=LAYERS):
 if kind=='iid': return np.eye(n)
 if kind=='common': return np.ones((n,n))
 if kind=='alternating':
  a=(-1.)**np.arange(n);return np.outer(a,a)
 if kind.startswith('ar'):
  rho=float(kind[2:]);return rho**abs(np.arange(n)[:,None]-np.arange(n))
 if kind=='block':
  b=np.equal(np.arange(n)//2,np.arange(n)[:,None]//2).astype(float);return .2*np.ones((n,n))+.8*b
 raise ValueError(kind)

def root_cov(c):
 v,q=np.linalg.eigh(c);return q@np.diag(np.sqrt(np.maximum(v,0)))

def learn_corr(samples):
 c=LedoitWolf().fit(samples).covariance_;sd=np.sqrt(np.diag(c));return c/sd[:,None]/sd[None,:]

class Objective:
 def __init__(self,model,method='nominal',sigma=4.,cov=None,alpha=.05,tau=.0005):
  self.model=model;self.method=method;self.sigma=sigma;self.cov=cov;self.tau=tau
  self.z=float(norm.ppf(1-alpha/len(model.w)));self.calls=0;self.trace=[]
 def __call__(self,d):
  self.calls+=1
  if self.method=='nominal':
   out=self.model.evaluate(d,jac=True);R,J=out['R'],out['J'];v=R;G=J
  else:
   # Central differences of the analytic optical sensitivity give the Hessian.
   h=.002;delta=np.eye(LAYERS)*h
   ds=np.vstack([d,d+delta,d-delta]);out=self.model.evaluate(ds,jac=True)
   R=out['R'][0];J=out['J'][0]
   H=((out['J'][1:1+LAYERS]-out['J'][1+LAYERS:])/(2*h)).transpose(1,2,0)
   if self.method=='envelope':
    a=np.sqrt(J*J+1e-18);sd=self.sigma*a.sum(axis=1)
    D=self.sigma*np.einsum('mjk,mj->mk',H,J/a)
   else:
    C=np.eye(LAYERS) if self.cov is None else self.cov
    u=J@C;sd=self.sigma*np.sqrt(np.maximum((u*J).sum(axis=1),0)+1e-24)
    D=self.sigma**2*np.einsum('mjk,mj->mk',H,u)/sd[:,None]
   v=R+self.z*sd;G=J+self.z*D
  a=v/self.tau;wt=np.exp(a-logsumexp(a));f=self.tau*logsumexp(a)
  return float(f),wt@G
 def callback(self,x):
  v=self(x)[0];self.trace.append(v)

def fit(model,method,start,cov=None,sigma=4.,maxiter=220):
 obj=Objective(model,method,sigma,cov);t=time.perf_counter()
 res=minimize(obj,start,method='L-BFGS-B',jac=True,bounds=[(25.,160.)]*LAYERS,
  options={'maxiter':maxiter,'ftol':1e-11,'gtol':2e-7,'maxls':35},callback=obj.callback)
 return {'d':res.x.tolist(),'objective':float(res.fun),'success':bool(res.success),
  'message':str(res.message),'nit':int(res.nit),'nfev':int(res.nfev),'calls_including_trace':obj.calls,
  'seconds':time.perf_counter()-t,'trace':obj.trace,'method':method}

def fit_cvar(model,start,errors,maxiter=220):
 tau=.0005;beta=.95;trace=[];calls=0
 def obj(x):
  nonlocal calls
  calls+=1;out=model.evaluate(x[:8]+errors,jac=True);R,J=out['R'],out['J']
  a=R/tau;u=logsumexp(a,axis=1);weights=np.exp(a-u[:,None]);g=tau*u
  dg=np.einsum('bm,bmj->bj',weights,J);h=(g-x[8])/tau
  from scipy.special import expit
  p=expit(h);f=x[8]+tau*np.logaddexp(0,h).mean()/(1-beta)
  gradient=np.r_[(p[:,None]*dg).mean(axis=0)/(1-beta),1-p.mean()/(1-beta)]
  return float(f),gradient
 def callback(x):trace.append(obj(x)[0])
 t=time.perf_counter();init=np.r_[start,.06]
 res=minimize(obj,init,method='L-BFGS-B',jac=True,bounds=[(25.,160.)]*8+[(0.,1.)],
  options={'maxiter':maxiter,'ftol':1e-11,'gtol':2e-7,'maxls':35},callback=callback)
 return {'d':res.x[:8].tolist(),'var_aux':float(res.x[8]),'objective':float(res.fun),
  'success':bool(res.success),'message':str(res.message),'nit':int(res.nit),
  'nfev':int(res.nfev),'calls_including_trace':calls,'seconds':time.perf_counter()-t,
  'trace':trace,'method':'cvar'}
