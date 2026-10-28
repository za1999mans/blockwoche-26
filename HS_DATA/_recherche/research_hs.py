"""Reproduzierbare Recherche öffentlicher Hochschulquellen (nur Standardbibliothek)."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json, re, sys, time, hashlib

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'cache'
if not CACHE.exists() and (ROOT/'cache_location.json').exists():
    CACHE=Path(json.loads((ROOT/'cache_location.json').read_text())['cache'])
BASE = 'https://www.hs-osnabrueck.de'
DATE = '2026-10-28'

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
    def all(self, tag=None, cls=None):
        for c in self.children:
            if isinstance(c, Node):
                if (tag is None or c.tag == tag) and (cls is None or cls in c.attrs.get('class','').split()): yield c
                yield from c.all(tag, cls)
    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c,Node) else c for c in self.children).split())
    def lines(self):
        if self.tag in ('script','style','nav','footer','noscript'): return ''
        block = self.tag in ('p','div','section','article','main','h1','h2','h3','h4','h5','li','tr','br','ul','ol','table','dl','dt','dd')
        t = ''.join(c.lines() if isinstance(c, Node) else c for c in self.children)
        if self.tag in ('td','th'): t += ' | '
        return ('\n' + t + '\n') if block else t

class Parser(HTMLParser):
    def __init__(self, data):
        super().__init__(convert_charrefs=True); self.root=Node(); self.cur=self.root; self.feed(data)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,attrs,self.cur); self.cur.children.append(n)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'): self.cur=n
    def handle_endtag(self,tag):
        n=self.cur
        while n.parent:
            if n.tag==tag: self.cur=n.parent; break
            n=n.parent
    def handle_data(self,data): self.cur.children.append(data)

def parse(s): return Parser(s).root
def mainnode(n): return next(n.all('main'),n)
def links(n,base):
    return [{'label':a.text(),'url':urljoin(base,a.attrs['href'])} for a in n.all('a') if a.attrs.get('href') and not a.attrs['href'].startswith(('#','javascript:'))]
def path(url): return CACHE / (hashlib.sha256(url.encode()).hexdigest()+'.json')
def fetch(url, force=False):
    CACHE.mkdir(parents=True,exist_ok=True)
    p=path(url)
    if p.exists() and not force:return json.loads(p.read_text())
    record={'url':url,'accessed':DATE}
    for attempt in range(3):
        try:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 (academic information research; low concurrency)'})
            with urlopen(req,timeout=55) as r:
                data=r.read(); record.update(final_url=r.url,status=r.status,content_type=r.headers.get('Content-Type',''))
            if 'pdf' in record['content_type'] or data.startswith(b'%PDF'):
                pdf=CACHE/(p.stem+'.pdf');pdf.write_bytes(data);record['pdf_path']=str(pdf)
            elif record['content_type'].startswith('image/'):
                record['binary_bytes']=len(data)
                ext='.png' if 'png' in record['content_type'] else '.jpg'
                asset=CACHE/(p.stem+ext);asset.write_bytes(data)
                record['image_path']=str(asset)
            else:
                record['html']=data.decode('utf-8','replace')
                if record['html'].lstrip().startswith(('[{','{"')):
                    record['json']=json.loads(record['html'])
                else:
                    n=parse(record['html']);m=mainnode(n)
                    record['title']=next(n.all('title'),n).text()
                    record['text']='\n'.join(t.strip() for t in m.lines().splitlines() if t.strip())
                    record['links']=links(m,record['final_url'])
            p.write_text(json.dumps(record,ensure_ascii=False,indent=2));return record
        except Exception as e:
            record['error']=str(e)
            if attempt<2:time.sleep(1+attempt)
    p.write_text(json.dumps(record,ensure_ascii=False,indent=2));return record

def batch(urls):
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending={pool.submit(fetch,u):u for u in dict.fromkeys(urls)}
        for f in as_completed(pending):
            r=f.result();print(json.dumps({k:r[k] for k in ('url','status','error') if k in r},ensure_ascii=False),flush=True)

def clean(n):
    n.children=[c for c in n.children if not isinstance(c,Node) or (c.tag not in ('nav','aside','script','style','footer','noscript') and c.attrs.get('id')!='hsos-navigation-menu' and not any(k in c.attrs.get('class','') for k in ('breadcrumb','hsos-navigation-menu','az-paging','az-filter')))]
    for c in n.children:
        if isinstance(c,Node):clean(c)
    return n

def document(r): return clean(mainnode(parse(r.get('html',''))))
def lines(r):return [t.strip() for t in document(r).lines().splitlines() if t.strip()]
def cached(url):
    p=path(url)
    return json.loads(p.read_text()) if p.exists() else {}

if __name__=='__main__':
    if sys.argv[1]=='fetch':batch(sys.argv[2:])
    elif sys.argv[1]=='refresh':
        for u in sys.argv[2:]:
            r=fetch(u,force=True);print(json.dumps({k:r[k] for k in ('url','status','error','image_path') if k in r},ensure_ascii=False))
    elif sys.argv[1]=='batch':batch(json.loads(Path(sys.argv[2]).read_text()))
    elif sys.argv[1]=='show':
        r=fetch(sys.argv[2]);print(r.get('text',r));print(json.dumps(r.get('links',[]),ensure_ascii=False,indent=2))
