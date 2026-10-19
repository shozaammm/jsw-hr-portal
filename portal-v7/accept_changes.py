"""Accept all tracked changes in a docx -> new docx."""
import sys, zipfile, re
from lxml import etree
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
q=lambda t:'{%s}%s'%(W,t)
src,dst=sys.argv[1],sys.argv[2]
zin=zipfile.ZipFile(src); zout=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=zin.read(it.filename)
    if it.filename in('word/document.xml','word/footnotes.xml','word/endnotes.xml') or re.match(r'word/(header|footer)\d*\.xml',it.filename):
        root=etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False))
        for tag in ('del','moveFrom'):
            for e in root.iter(q(tag)):
                pass
            for e in list(root.iter(q(tag))):
                par=e.getparent()
                if par.tag==q('rPr'):
                    # deleted paragraph mark: merge with next paragraph
                    p=par.getparent()
                    if p.tag==q('pPr'):
                        # Word keeps the *following* paragraph's properties for the merged paragraph
                        para=p.getparent(); nxt=para.getnext()
                        par.remove(e)
                        if nxt is not None and nxt.tag==q('p'):
                            npr=nxt.find(q('pPr')); k=0 if npr is None else 1
                            for ch in list(para):
                                if ch.tag!=q('pPr'): nxt.insert(k,ch); k+=1
                            para.getparent().remove(para)
                        continue
                    par.remove(e); continue
                par.remove(e)
        for tag in ('ins','moveTo'):
            for e in list(root.iter(q(tag))):
                par=e.getparent()
                if par.tag==q('rPr'): par.remove(e); continue
                i=par.index(e)
                for ch in list(e): par.insert(i,ch); i+=1
                par.remove(e)
        for tag in ('rPrChange','pPrChange','sectPrChange','tblPrChange','trPrChange','tcPrChange','numberingChange'):
            for e in list(root.iter(q(tag))): e.getparent().remove(e)
        # deleted table rows
        for tr in list(root.iter(q('tr'))):
            trpr=tr.find(q('trPr'))
        data=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
    zout.writestr(it,data)
zout.close()
