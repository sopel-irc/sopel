"""
wikipedia.py - Willie Wikipedia Module
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""

import re, urllib, gzip, StringIO
import willie.web as web

wikiuri = 'http://%s.wikipedia.org/wiki/%s'
# wikisearch = 'http://%s.wikipedia.org/wiki/Special:Search?' \
#                            + 'search=%s&fulltext=Search'

r_tr = re.compile(r'(?ims)<tr[^>]*>.*?</tr>')
r_paragraph = re.compile(r'(?ims)<p[^>]*>.*?</p>|<li(?!n)[^>]*>.*?</li>')
r_tag = re.compile(r'<(?!!)[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')
r_redirect = re.compile(
    r'(?ims)class=.redirectText.>\s*<a\s*href=./wiki/([^"/]+)'
)

abbrs = ['etc', 'ca', 'cf', 'Co', 'Ltd', 'Inc', 'Mt', 'Mr', 'Mrs',
            'Dr', 'Ms', 'Rev', 'Fr', 'St', 'Sgt', 'pron', 'approx', 'lit',
            'syn', 'transl', 'sess', 'fl', 'Op', 'Dec', 'Brig', 'Gen'] \
    + list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') \
    + list('abcdefghijklmnopqrstuvwxyz')
t_sentence = r'^.{5,}?(?<!\b%s)(?:\.(?=[\[ ][A-Z0-9]|\Z)|\Z)'
r_sentence = re.compile(t_sentence % r')(?<!\b'.join(abbrs))

def unescape(s):
    s = s.replace('&gt;', '>')
    s = s.replace('&lt;', '<')
    s = s.replace('&amp;', '&')
    s = s.replace('&#160;', ' ')
    return s

def text(html):
    html = r_tag.sub('', html)
    html = r_whitespace.sub(' ', html)
    return unescape(html).strip()

def search(term):
    try: import search
    except ImportError, e:
        print e
        return term

    if isinstance(term, unicode):
        term = term.encode('utf-8')
    else: term = term.decode('utf-8')

    term = term.replace('_', ' ')
    try: uri = search.google_search('site:en.wikipedia.org %s' % term)
    except IndexError: return term
    if uri:
        return uri[len('http://en.wikipedia.org/wiki/'):]
    else: return term

def wikipedia(term, language='en', last=False):
    global wikiuri
    if not '%' in term:
        if isinstance(term, unicode):
            t = term.encode('utf-8')
        else: t = term
        q = urllib.quote(t)
        u = wikiuri % (language, q)
        bytes = web.get(u)
    else: bytes = web.get(wikiuri % (language, term))

    if bytes.startswith('\x1f\x8b\x08\x00\x00\x00\x00\x00'):
        f = StringIO.StringIO(bytes)
        f.seek(0)
        gzip_file = gzip.GzipFile(fileobj=f)
        bytes = gzip_file.read()
        gzip_file.close()
        f.close()

    bytes = r_tr.sub('', bytes)

    if not last:
        r = r_redirect.search(bytes[:4096])
        if r:
            term = urllib.unquote(r.group(1))
            return wikipedia(term, language=language, last=True)

    paragraphs = r_paragraph.findall(bytes)

    if not paragraphs:
        if not last:
            term = search(term)
            return wikipedia(term, language=language, last=True)
        return None

    # Pre-process
    paragraphs = [para for para in paragraphs
                      if (para and 'technical limitations' not in para
                                  and 'window.showTocToggle' not in para
                                  and 'Deletion_policy' not in para
                                  and 'Template:AfD_footer' not in para
                                  and not (para.startswith('<p><i>') and
                                              para.endswith('</i></p>'))
                                  and not 'disambiguation)"' in para)
                                  and not '(images and media)' in para
                                  and not 'This article contains a' in para
                                  and not 'id="coordinates"' in para
                                  and not 'class="thumb' in para]
                                  # and not 'style="display:none"' in para]

    for i, para in enumerate(paragraphs):
        para = para.replace('<sup>', '|')
        para = para.replace('</sup>', '|')
        paragraphs[i] = text(para).strip()

    # Post-process
    paragraphs = [para for para in paragraphs if
                      (para and not (para.endswith(':') and len(para) < 150))]

    para = text(paragraphs[0])
    m = r_sentence.match(para)

    if not m:
        if not last:
            term = search(term)
            return wikipedia(term, language=language, last=True)
        return None
    sentence = m.group(0)

    maxlength = 275
    if len(sentence) > maxlength:
        sentence = sentence[:maxlength]
        words = sentence[:-5].split(' ')
        words.pop()
        sentence = ' '.join(words) + ' [...]'

    if (('using the Article Wizard if you wish' in sentence)
     or ('or add a request for it' in sentence)
     or ('in existing articles' in sentence)):
        if not last:
            term = search(term)
            return wikipedia(term, language=language, last=True)
        return None

    sentence = '"' + sentence.replace('"', "'") + '"'
    sentence = sentence.decode('utf-8').encode('utf-8')
    wikiuri = wikiuri.decode('utf-8').encode('utf-8')
    term = term.decode('utf-8').encode('utf-8')
    return sentence + ' - ' + (wikiuri % (language, term))

def wik(willie, trigger):
    """Look up something on Wikipedia"""
    origterm = trigger.groups()[1]
    if not origterm:
        return willie.say('Perhaps you meant ".wik Zen"?')
    origterm = origterm.encode('utf-8')

    term = urllib.unquote(origterm)
    language = 'en'
    if term.startswith(':') and (' ' in term):
        a, b = term.split(' ', 1)
        a = a.lstrip(':')
        if a.isalpha():
            language, term = a, b
    term = term[0].upper() + term[1:]
    term = term.replace(' ', '_')

    try: result = wikipedia(term, language)
    except IOError:
        args = (language, wikiuri % (language, term))
        error = "Can't connect to %s.wikipedia.org (%s)" % args
        return willie.say(error)

    if result is not None:
        willie.say(result)
    else: willie.say('Can\'t find anything in Wikipedia for "%s".' % origterm)

wik.commands = ['wiki', 'wik']
wik.priority = 'high'

if __name__ == '__main__':
    print __doc__.strip()
