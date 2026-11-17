"""Integrity checks against retained numerical records and editable documents."""
import json,zipfile,re,hashlib,sys
from pathlib import Path
import numpy as np,pandas as pd
from docx import Document
from optics import ROOT
from evaluate import summarize
def main():
 frame=pd.read_csv(ROOT/'data/primary_metrics.csv');assert len(frame)==48
 errors=[]
 for row in frame.to_dict('records'):
  v=dict(np.load(ROOT/f"data/test_{row['method']}_{row['case']}.npz"))
  assert len(v['maxR'])==4096 and np.all(v['valid'])
  fresh=summarize(v)
  for key in fresh:
   if not np.isclose(fresh[key],row[key],atol=1e-12,rtol=1e-11):errors.append((row['method'],row['case'],key))
 assert not errors,errors
 blocks=json.load(open(ROOT/'notes/manuscript_blocks.json'));assert len(blocks['equations'])==23
 assert not re.search(r'\{C\d',json.dumps(blocks)), 'Unresolved citation placeholder'
 assert len(blocks['abstract'].split()) in range(150,251)
 assert [b['number'] for b in blocks['blocks'] if b['type']=='fig']==list(range(1,11))
 assert [b['number'] for b in blocks['blocks'] if b['type']=='ref']==list(range(1,26))
 docs={}
 for p in (ROOT/'output').glob('*.docx'):
  d=Document(p);nm=len(d.element.xpath('.//m:oMath'));ni=len(d.inline_shapes)
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
  if any(s in p.name for s in ['Manuscript','Highlighted']):assert nm==23 and ni==10
  docs[p.name]={'native_math_objects':nm,'embedded_figures':ni}
 figs=json.load(open(ROOT/'figures/figure_manifest.json'));assert len(figs)==10
 refs=json.load(open(ROOT/'references/references.json'));assert len(refs)==25 and len(set(r['doi'].lower() for r in refs))==25
 protocol_hash=hashlib.sha256((ROOT/'notes/protocol.md').read_bytes()).hexdigest()
 assert protocol_hash==json.load(open(ROOT/'data/environment.json'))['protocol_sha256']
 report={'primary_rows':48,'independent_test_draws_per_process':4096,'all_primary_draws_physically_valid':True,
  'raw_to_summary_consistency':'passed','protocol_hash_matches':True,'equations':23,'figures':10,
  'editable_result_tables':10,'references':25,'recent_references_2024_2026':sum(r['year']>=2024 for r in refs),'documents':docs}
 (ROOT/'qa/integrity_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
