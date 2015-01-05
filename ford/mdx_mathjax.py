"""md_mathjax is a simple extension of the Python implementation of Markdown
author: Man YUAN
homepage: https://github.com/epsilony/md_mathjax
"""

from markdown.util import AtomicString
from markdown.util import etree
from markdown.inlinepatterns import Pattern
from markdown import Extension

class MathJaxPattern(Pattern):
    groups = 2, 3, 4
    start_end = None
    
    def __init__ (self, start_end=None, groups=None):
        if start_end is not None:
            self.start_end = start_end
        if groups is not None:
            self.groups = groups
        pattern = r'(?<!\\)(%s)(.+?)(?<!\\)(%s)' % (self.start_end)
        Pattern.__init__(self, pattern)

    def handleMatch(self, m):
        node = etree.Element(None)
        text = ''
        for group in self.groups:
            text += m.group(group)
        node.text = AtomicString(text)
        return node;

class MathJaxInlinePattern(MathJaxPattern):    
    start_end = r'\\\(', r'\\\)'
        

class BraketPattern(MathJaxPattern):  
    start_end = r'\\\[', r'\\\]'

class DoubleDollarPattern(MathJaxPattern):
    start_end = r'\$\$', r'\$\$'

class BeginEndPattern(MathJaxPattern):
    start_end = r'\\begin\{(.+?)\}', r'\\end\{\3\}'
    groups = 2, 4, 5
    
class MathJaxExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('mathjax_invironment', BeginEndPattern(), '<escape')
        md.inlinePatterns.add('mathjax_bracket', BraketPattern(), '<escape')
        md.inlinePatterns.add('mathjax_double_dollar', DoubleDollarPattern(), '<escape')
        md.inlinePatterns.add('mathjax_inline', MathJaxInlinePattern(), '<escape')
        
def makeExtension(configs=None):
    return MathJaxExtension(configs)
