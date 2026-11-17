from docx import Document
from docx.shared import Inches,Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import copy,re
TITLE=""
omml=[]

def init_doc():
 doc=Document();sec=doc.sections[0];sec.page_height=Inches(11);sec.page_width=Inches(8.5);sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.7);sec.left_margin=Cm(1.8);sec.right_margin=Cm(1.8);sec.header_distance=Cm(.7);sec.footer_distance=Cm(.7)
 for sty in ['Normal','Title','Subtitle','Heading 1','Heading 2','Caption']:
  s=doc.styles[sty];s.font.name='Times New Roman';s.font.color.rgb=RGBColor(0,0,0);s.element.rPr.rFonts.set(qn('w:eastAsia'),'Times New Roman')
 for sty in doc.styles:
  for e in sty.element.xpath('.//w:pBdr'):e.getparent().remove(e)
  if sty.type==1:
   rf=sty.element.get_or_add_rPr().find(qn('w:rFonts'))
   if rf is None:rf=OxmlElement('w:rFonts');sty.element.get_or_add_rPr().append(rf)
   for key in list(rf.attrib):
    if 'theme' in key.lower():del rf.attrib[key]
   for key in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+key),'Times New Roman')
 normal=doc.styles['Normal'];normal.font.size=Pt(11);normal.paragraph_format.line_spacing=1.08;normal.paragraph_format.space_after=Pt(5)
 for sty,size in [('Title',17),('Heading 1',13),('Heading 2',11.5)]:
  s=doc.styles[sty];s.font.size=Pt(size);s.font.bold=True;s.paragraph_format.space_before=Pt(10);s.paragraph_format.space_after=Pt(5);s.paragraph_format.keep_with_next=True
 doc.styles['Caption'].font.size=Pt(10);doc.styles['Caption'].font.italic=False;doc.styles['Caption'].font.bold=False
 f=sec.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=f.add_run();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
 doc.core_properties.title=TITLE;doc.core_properties.author='';doc.core_properties.subject='Correlation uncertainty in optical coating design';doc.core_properties.keywords='optical coatings; correlation uncertainty; robust inverse design; nonlinear reliability'
 return doc

def highlight(para,on):
 if on:
  for r in para.runs:r.font.highlight_color=WD_COLOR_INDEX.YELLOW

def par(doc,text,style=None,on=False):
 p0=doc.add_paragraph(style=style);p0.paragraph_format.widow_control=True
 parts=re.split(r'(10−\d+|nm−\d+|\bs2\b)',text)
 for part in parts:
  if re.fullmatch(r'(?:E_b|D_p|R_0|c_f|d_h)',part):
   base,sub=part.split('_');p0.add_run(base);p0.add_run(sub).font.subscript=True
  elif re.fullmatch(r'(10|nm)−\d+',part):
   base,power=part.split('−');p0.add_run(base);p0.add_run('−'+power).font.superscript=True
  elif part=='s2':
   p0.add_run('s');p0.add_run('2').font.superscript=True
  else:p0.add_run(part)
 if not style:p0.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
 for e in p0._p.xpath('./w:pPr/w:pBdr'):e.getparent().remove(e)
 highlight(p0,on);return p0

def clean_table(t,widths=None):
 t.autofit=False
 pr=t._tbl.tblPr;b=OxmlElement('w:tblBorders')
 for n in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+n);e.set(qn('w:val'),'nil');b.append(e)
 pr.append(b)
 for row in t.rows:
  trpr=row._tr.get_or_add_trPr();n=OxmlElement('w:cantSplit');trpr.append(n)
  for j,c in enumerate(row.cells):
   if widths:c.width=Inches(widths[j])
   for p0 in c.paragraphs:
    p0.paragraph_format.space_after=Pt(3);p0.paragraph_format.space_before=Pt(3);p0.paragraph_format.line_spacing=1.0
    for r in p0.runs:r.font.name='Times New Roman';r.font.size=Pt(9.5)
 if widths:
  for j,w in enumerate(widths):t.columns[j].width=Inches(w)

def set_edge(cell,edge,val='single',size='5'):
 pr=cell._tc.get_or_add_tcPr();bs=pr.find(qn('w:tcBorders'))
 if bs is None:bs=OxmlElement('w:tcBorders');pr.append(bs)
 e=OxmlElement('w:'+edge);e.set(qn('w:val'),val);e.set(qn('w:sz'),size);e.set(qn('w:color'),'000000');bs.append(e)

def add_table(doc,b,hilite=False):
 cap=par(doc,b['title'],'Caption',hilite and b.get('rev',False));cap.paragraph_format.keep_with_next=True
 t=doc.add_table(rows=1,cols=len(b['head']));
 for c,tx in zip(t.rows[0].cells,b['head']):c.text=tx
 for row in b['rows']:
  for c,tx in zip(t.add_row().cells,row):c.text=str(tx)
 clean_table(t,b.get('widths'))
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 t._tbl.tblPr.append(borders)
 for ri,row in enumerate(t.rows):
  for ci,c in enumerate(row.cells):
   for pi,p0 in enumerate(c.paragraphs):
    p0.paragraph_format.keep_with_next=(ri==0) if len(t.rows)>9 else not(ri==len(t.rows)-1 and ci==len(row.cells)-1 and pi==len(c.paragraphs)-1)
    p0.paragraph_format.keep_together=True
 for c in t.rows[0].cells:
  for r in c.paragraphs[0].runs:r.bold=True
  sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF1');c._tc.get_or_add_tcPr().append(sh)
 for row in t.rows:
  for c in row.cells:
   margins=OxmlElement('w:tcMar')
   for key in ['top','bottom','left','right']:
    v=OxmlElement('w:'+key);v.set(qn('w:w'),'65' if key in ['top','bottom'] else '85');v.set(qn('w:type'),'dxa');margins.append(v)
   c._tc.get_or_add_tcPr().append(margins)
   va=OxmlElement('w:vAlign');va.set(qn('w:val'),'center');c._tc.get_or_add_tcPr().append(va)
 rep=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(rep)
 for j in range(len(b['head'])):
  values=[str(r[j]) for r in b['rows']]
  if values and sum(bool(re.match(r'^\d',v)) for v in values)/len(values)>.65:
   for row in t.rows:
    for pp in row.cells[j].paragraphs:pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
 if b.get('note'):
  p0=par(doc,b['note']);p0.paragraph_format.space_before=Pt(4);p0.paragraph_format.space_after=Pt(6)
  for r in p0.runs:r.font.size=Pt(9)
 else:
  pp=doc.add_paragraph();pp.paragraph_format.space_before=Pt(0);pp.paragraph_format.space_after=Pt(0);pp.paragraph_format.line_spacing=Pt(4);pp.add_run().font.size=Pt(4)
 return t

def add_eq(doc,index,rev=False,hilite=False):
 t=doc.add_table(rows=1,cols=2);clean_table(t,[5.95,.85]);left,right=t.rows[0].cells;p0=left.paragraphs[0];p0.alignment=WD_ALIGN_PARAGRAPH.CENTER;p0.paragraph_format.space_after=Pt(2);p0.paragraph_format.space_before=Pt(2)
 x=copy.deepcopy(omml[index]);p0._p.append(x)
 # Normalize native math for both Word and LibreOffice. Fixed non-round
 # delimiters avoid an importer bug with unsupported growing end characters.
 for acc in list(x.findall('.//'+qn('m:acc'))):
  pr=acc.find(qn('m:accPr'));ch=pr.find(qn('m:chr')) if pr is not None else None
  if ch is not None and ch.get(qn('m:val')) in ['‾','¯','̅']:
   bar=OxmlElement('m:bar');bp=OxmlElement('m:barPr');pos=OxmlElement('m:pos');pos.set(qn('m:val'),'top');bp.append(pos);bar.append(bp);bar.append(copy.deepcopy(acc.find(qn('m:e'))));acc.getparent().replace(acc,bar)
 for d in reversed(list(x.findall('.//'+qn('m:d')))):
  pr=d.find(qn('m:dPr'));beg=pr.find(qn('m:begChr'));end=pr.find(qn('m:endChr'));bc=beg.get(qn('m:val')) if beg is not None else '(';ec=end.get(qn('m:val')) if end is not None else ')'
  if (bc,ec)==('(',')'):continue
  parent=d.getparent();position=parent.index(d);new=[]
  def literal(char):
   r=OxmlElement('m:r');rr=OxmlElement('m:rPr');sty=OxmlElement('m:sty');sty.set(qn('m:val'),'p');rr.append(sty);r.append(rr);tx=OxmlElement('m:t');tx.text=char;r.append(tx);return r
  if bc:new.append(literal(bc))
  for e in d.findall(qn('m:e')):new.extend(copy.deepcopy(child) for child in e)
  if ec:new.append(literal(ec))
  parent.remove(d)
  for j,item in enumerate(new):parent.insert(position+j,item)
 for r in x.findall('.//'+qn('m:r')):
  pr=r.find(qn('w:rPr'))
  if pr is None:
   pr=OxmlElement('w:rPr');m_pr=r.find(qn('m:rPr'));r.insert(1 if m_pr is not None else 0,pr)
  fonts=OxmlElement('w:rFonts')
  for key in ['ascii','hAnsi','eastAsia','cs']:fonts.set(qn('w:'+key),'Latin Modern Math')
  pr.append(fonts)
  sz=OxmlElement('w:sz');sz.set(qn('w:val'),'21');pr.append(sz)
  if rev and hilite:
   hl=OxmlElement('w:highlight');hl.set(qn('w:val'),'yellow');pr.append(hl)
 pnum=right.paragraphs[0];pnum.alignment=WD_ALIGN_PARAGRAPH.RIGHT;pnum.add_run(f'({index+1})').font.size=Pt(10.5)
 for c in t.rows[0].cells:
  va=OxmlElement('w:vAlign');va.set(qn('w:val'),'center');c._tc.get_or_add_tcPr().append(va)
