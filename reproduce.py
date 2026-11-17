"""Offline reproduction. Default regenerates reports; --all recomputes experiments."""
import argparse,subprocess,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');a=p.parse_args()
 env=os.environ.copy()
 for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:env[key]='1'
 scripts=['assemble_references.py']
 if a.all:scripts+=['run_designs.py','evaluate.py','secondary.py','exploratory.py']
 scripts+=['postprocess.py','figures.py','build_documents.py','audit.py']
 for s in scripts:
  print('Running',s,flush=True);subprocess.run([sys.executable,str(ROOT/'code'/s)],check=True,env=env,cwd=ROOT)
 print('Completed. PDF rendering requires LibreOffice/Poppler or another Word-compatible renderer.')
if __name__=='__main__':main()
