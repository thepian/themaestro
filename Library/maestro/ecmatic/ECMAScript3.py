"""
A grammar for parsing a tiny CSS-like language, plus a transformer for it.
"""
from pymeta.grammar import OMeta
from itertools import chain

ECMAScriptGrammar = """

grammar = line*:l emptyline* end -> l

hspace    = ' ' | '\t'
vspace    = '\n'
optspace  = ?(self.parenthesis) (hspace | '\\'? vspace | comment)* | (hspace | '\\' vspace)* comment?
mandspace = ?(self.parenthesis) (hspace | '\\'? vspace | comment)+ | (hspace | '\\' vspace)+ comment?

indentation = hspace*:i ?(len(i) == self.indent_stack[-1])
indent      = hspace*:i ?(len(i) > self.indent_stack[-1]) !(self.indent_stack.append(len(i)))
dedent      = !(self.dedent())

comment  = '#' line_rest:c -> ['comment', c]
emptyline = hspace* ('\\' | comment)?:c vspace
block     = emptyline* indent stmt:s optspace (vspace | end) line*:l dedent -> [s] + l
line      = emptyline*:e indentation stmt:s optspace (vspace | end) -> s
line_rest = (~vspace :x)*:x -> ''.join(x)

"""
ECMAScript = OMeta.makeGrammar(ECMAScriptGrammar, globals(), name="ECMAScript")

