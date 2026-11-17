from pathlib import Path
import json,re,csv,html
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'references'
def fallback(n,doi,title,authors,journal,vol,pages,year,source):
 m={'DOI':doi,'title':[title],'author':[{'given':g,'family':f} for g,f in authors],
  'container-title':[journal],'volume':vol,'page':pages,'published':{'date-parts':[[year]]},
  'metadata_source':source,'type':'journal-article'}
 (D/f'crossref_{n:02}.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
fallback(1,'10.1007/s10043-009-0031-6','Spiral search method for designing a wide angular broadband visible antireflection coating',
 [('Yeuh-Yeong','Liou'),('Zhi-Wei','Wei'),('Li-Rang','Wang'),('Chi-Chang','Liu'),('Chin-Chiuan','Kuo'),('Cheng-Chung','Jaing'),('Cheng-Chung','Lee')],
 'Optical Review','16','176-179',2009,'Publisher article record; Crossref returned HTTP429')
fallback(4,'10.1364/OE.471998','Statistical information enhanced robust design method of optical thin film',
 [('Jianglin','Dai'),('Gong','Zhang'),('Shigeng','Song'),('Zeyu','Deng'),('Zihan','Wei')],
 'Optics Express','30','36826-36838',2022,'Author institution UWS and publisher abstract; Crossref returned HTTP429')
fallback(15,'10.29026/oea.2024.240062','OptoGPT: A foundation model for inverse design in optical multilayer thin film structures',
 [('Taigao','Ma'),('Haozhu','Wang'),('L. Jay','Guo')],'Opto-Electronic Advances','7','240062',2024,
 'Publisher and University of Michigan author publication records; Crossref returned HTTP429')
fallback(22,'10.1080/01621459.1927.10502953','Probable Inference, the Law of Succession, and Statistical Inference',
 [('Edwin B.','Wilson')],'Journal of the American Statistical Association','22','209-212',1927,
 'Publisher and JSTOR primary issue records; Crossref returned HTTP429')
(D/'crossref_23.json').write_text((D/'crossref_23_sagd.json').read_text())
urls=[
'https://link.springer.com/article/10.1007/s10043-009-0031-6',
'https://pmc.ncbi.nlm.nih.gov/articles/PMC11995089/',
'https://doi.org/10.1109/4235.738986',
'https://research-portal.uws.ac.uk/en/publications/statistical-information-enhanced-robust-design-method-of-optical-/',
'https://www.sciencedirect.com/science/article/pii/S0030399223002268',
'https://www.mdpi.com/2079-6412/9/12/809',
'https://doi.org/10.1117/12.3106760',
'https://www.nature.com/articles/s41598-026-65513-5',
'https://pmc.ncbi.nlm.nih.gov/articles/PMC11833107/',
'https://authors.library.caltech.edu/records/q46ez-wtx38',
'https://www.sciencedirect.com/science/article/abs/pii/S0143816624006043',
'https://opg.optica.org/ao/abstract.cfm?uri=ao-65-12-4018',
'https://opg.optica.org/ol/abstract.cfm?uri=ol-51-7-1696',
'https://opg.optica.org/oe/abstract.cfm?uri=oe-33-5-10057',
'https://www.oejournal.org/article/doi/10.29026/oea.2024.240062',
'https://pmc.ncbi.nlm.nih.gov/articles/PMC11501231/',
'https://pmc.ncbi.nlm.nih.gov/articles/PMC10796781/',
'https://publications.physics.muni.cz/articles/AO54_9108-1063',
'https://opg.optica.org/josa/abstract.cfm?uri=josa-55-10-1205',
'https://www.ledoit.net/Well-conditioned2004.pdf',
'https://doi.org/10.21314/JOR.2000.038',
'https://www.tandfonline.com/doi/abs/10.1080/01621459.1927.10502953',
'https://onlinelibrary.wiley.com/doi/full/10.1002/lpor.71366',
'https://www.sciencedirect.com/science/article/pii/S2666950126001719',
'https://www.mdpi.com/2673-3951/7/3/117']
claims=[
'Wide-angle visible antireflection optimization is established in Optical Review; no numerical equivalence claimed',
'Review of optimization and deep learning for one-dimensional multilayer inverse design',
'Robust evolutionary design of optical coatings predates current ML methods',
'Mean and standard deviation objectives for robust optical thin-film design already exist',
'Taylor-statistical treatment of correlated and uncorrelated broadband-monitoring errors already exists',
'Thickness-error correlations can be harmful or self-compensating during monitoring',
'Conference abstract describes yield optimization for correlated BBOM errors; not a journal or reproduced baseline',
'Flow matching with a CVaR deposition-error objective already exists; no first risk-aware inverse-design claim',
'Surrogate sensitivity and in-situ reoptimization studied for waveguide facet coatings, a different geometry',
'Coating optimization can include fabrication tolerance and MCMC thickness inference',
'Adaptive multiobjective coating design and learned optimization initialization already exist',
'Active-learning discrete-index antireflection design; different material/design degrees of freedom',
'Tandem residual inverse design of a bilayer metamaterial; not a homogeneous planar coating comparison',
'Deep-learning optical inversion of coatings; not used as a black-box performance baseline',
'Transformer models address flexible multilayer inverse design',
'Differentiable-solver neural design with systematic and random fabrication errors is established',
'Optical-constant database provenance; CC0 YAML files retained separately',
'Specific measured hafnia complex dispersion used for the forward model',
'Bulk fused-silica Sellmeier formula used as a transparent film proxy',
'Shrinkage covariance estimator used for the synthetic witness-data baseline',
'CVaR variational objective used for an in-house sampled control',
'Wilson binomial score interval foundation; formula independently implemented',
'Sharpness-aware gradient design with differentiable transfer matrices addresses perturbation-tolerant thin films; distinct from covariance ambiguity',
'Application-specific losses for coating spectral prediction; distinct from correlation uncertainty',
'Constraint-aware multiobjective DUV curved-coating synthesis is established; different uncertainty target']
full={2:'Full primary review introduction and inverse-design taxonomy read',9:'Full primary sensitivity methods and model limitations read',
 16:'Full primary introduction and fabrication-aware method read',18:'Primary author-institution abstract and CC0 database film/model definition; full article unavailable',
 19:'Primary material formula reproduced in CC0 source YAML',20:'Author-hosted abstract and bibliographic record; standard shrinkage estimator supplied by scikit-learn'}
refs=[];ev=[];bib=[]
for n in range(1,26):
 m=json.loads((D/f'crossref_{n:02}.json').read_text())
 if n==7:m.update({'container-title':['Proceedings of SPIE'],'volume':'14107','page':'141070D','type':'proceedings-article'})
 if n==10:m['page']='11751-11762'
 if n==12:m['page']='4018-4030'
 if n==13:m['page']='1696-1699'
 if n==14:m['page']='10057-10068'
 if n==18:m['page']='9108-9119'
 if n==19:m['page']='1205-1208';m['title']=['Interspecimen comparison of the refractive index of fused silica']
 title=html.unescape(m['title'][0]);journal=html.unescape(m['container-title'][0]);year=m['published']['date-parts'][0][0]
 initials=lambda s:''.join(t[0]+'.' for t in re.findall(r'[^\W\d_]+',s,flags=re.UNICODE))
 author=', '.join(a['family']+', '+initials(a.get('given','')) for a in m['author'])
 pg=m.get('page',m.get('article-number',''));v=m.get('volume','');doi=m['DOI']
 text=f'{author}: {title}. {journal} {v}, {pg} ({year}). https://doi.org/{doi}'
 if n==7:text+=' [Conference paper]'
 refs.append(dict(number=n,text=text,doi=doi,title=title,year=year,metadata=m))
 level=full.get(n,'Primary publisher/author abstract or indexed primary abstract and bibliographic metadata')
 if n==3:level='Publisher-deposited Crossref title and metadata; no detailed algorithm or performance claim relied upon'
 if n==7:level='Publisher-deposited Crossref metadata; author conference abstract indexed by ADS; publisher full-text access failed'
 if n==22:level='Primary publisher/JSTOR bibliographic record; score interval independently derived, no textual quotation'
 ev.append(dict(number=n,doi=doi,primary_url=urls[n-1],access_level=level,supported_claim=claims[n-1],checked='2026-11-05',
  limitation='No reproduced numerical result or superiority claim relative to this paper'))
 typ='inproceedings' if n==7 else 'article'
 bib.append('@'+typ+'{ref'+str(n)+',\n  author = {'+' and '.join(a['family']+', '+a.get('given','') for a in m['author'])+'},\n  title = {'+title+'},\n  '+('booktitle' if n==7 else 'journal')+' = {'+journal+'},\n  year = {'+str(year)+'},\n  volume = {'+v+'},\n  pages = {'+pg+'},\n  doi = {'+doi+'}\n}')
(D/'references.json').write_text(json.dumps(refs,ensure_ascii=False,indent=2));(D/'references.bib').write_text('\n\n'.join(bib))
(D/'reference_evidence.json').write_text(json.dumps(ev,ensure_ascii=False,indent=2))
with open(D/'reference_evidence.csv','w',newline='') as f:w=csv.DictWriter(f,fieldnames=ev[0]);w.writeheader();w.writerows(ev)
print(len(refs),'references;',sum(r['year']>=2024 for r in refs),'published 2024–2026')
