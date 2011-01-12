from __future__ import with_statement
__author__ = 'henrikvendelbo'
from pymeta.grammar import OMeta
from pymeta.runtime import ParseError as OMetaParseError
import os, re

"""

Comments:
    When found in odd places comments are taken to be disabled bits of code, and are dropped.
    
    Comments before or after statements are preserved in the AST
    Comments in function declaration arguments are preserved in the AST
"""

def compile(source):
    try:
        tmp,error = Grammar(source).apply('grammar')
    except OMetaParseError, e:
        raise ParseError(e.formatError(source))
    try:
        return Grammar(tmp).apply('grammar')[0]
    except OMetaParseError, e:
        raise ParseError(e.formatError(source))

grammar_path = os.path.join(os.path.dirname(__file__), 'basic.ometa')
basic_grammar = None
with open(grammar_path, 'r') as f:
    basic_grammar = f.read()

class ParseError(Exception):
    pass

def emptyAst():    
    return ["Empty"]
    
def ast(startPos, tp, attributes, children):
    return [tp, attributes] + children
    
def p(out):
    print out
    return out


class Grammar(OMeta.makeGrammar(basic_grammar, {
 "p": p,
 "_fromIdx": 0,
 "ucSpacesRE": re.compile(r"\s")

})):
    keywords = set(
     ("break","do","instanceof","typeof","case","else","new","var","catch","finally",
      "return", "void", "continue", "for", "switch", "while", "debugger", "function",
      "this", "with", "default", "if", "throw", "delete", "in", "try" ))
    nonStrictFutureKws = set(
     ("class", "enum", "extends", "super", "const", "export", "import"))
    strictFutureKws = set(
     ("implements", "let", "private", "public", "interface", "package",
      "protected", "static", "yield" ))
      

    extraKeywords = set(('and', 'as',  'class', 'continue',
        'def', 'default', 'del', 'delete', 'do', 'elif',
        'false', 'finally', 'function',  'is', 'instanceof',
        'new', 'not', 'null', 'or', 'pass', 'raise', 'return', 'switch',
        'this', 'throw', 'true', 'typeof', 'var', 'void',
        'yield',))
    hex_digits = '0123456789abcdef'
    
    strictmode = False

    def is_keyword(self, keyword):
        return keyword in self.keywords

    def is_future(self,name):
        "Is the attribute name reserved"
        if self.strictmode:
            return name in self.strictFutureKws
        return name in self.nonStrictFutureKws

    def is_reserved(self,name):
        "Is the variable/function name reserved"
        return self.is_keyword(name) or self.is_future(name)

    def eatWhitespace(self):
        """
        Consume input until a non-whitespace character is reached.
        """
        consumingComment = False
        while True:
            try:
                c, e = self.input.head()
            except EOFError, e:
                break
            t = self.input.tail()
            if c.isspace() or consumingComment:
                self.input = t
                if c == '\n':
                    consumingComment = False
            elif c == '#':
                consumingComment = True
            else:
                break
        return True, e
    rule_spaces = eatWhitespace

    def ast(self, tp, *children, **attributes):
        return [tp, attributes] + [c for c in children]

    
translator_path = os.path.join(os.path.dirname(__file__), 'basic-translator.ometa')
pyva_translator = None
with open(translator_path, 'r') as f:
    pyva_translator = f.read()
    
class Translator(OMeta.makeGrammar(pyva_translator, {})):
    op_map = {
        'not': '!',
        'del': 'delete ',
    }
    binop_map = {
        'or': '||',
        'and': '&&',
        'is': '===',
        'is not': '!===',
    }
    name_map = {
        'None': 'null',
        'True': 'true',
        'False': 'false',
    }

    def __init__(self, *args, **kwargs):
        super(Translator, self).__init__(*args, **kwargs)
        self.indentation = 0
        self.local_vars = set()
        self.global_vars = set()
        self.var_stack = []
        self.temp_var_id = 0

    def make_temp_var(self, name, prefix='_$tmp'):
        self.temp_var_id += 1
        return '%s%s_%s' % (prefix, self.temp_var_id, name)

    def indent(self):
        self.indentation += 1
        return self.indentation

    def dedent(self):
        self.indentation -= 1

    def is_pure_var_name(self, var):
        return '.' not in var and '[' not in var

    def register_var(self, var):
        if self.is_pure_var_name(var) and var not in self.global_vars:
            self.local_vars.add(var)

    def register_vars(self, vars):
        for var in vars:
            self.register_var(var)

    def register_globals(self, vars):
        self.global_vars.update([var for var in vars if self.is_pure_var_name(var)])
        self.local_vars -= self.global_vars

    def push_vars(self):
        self.var_stack.append((self.local_vars, self.global_vars))
        self.local_vars = set()
        self.global_vars = set()

    def pop_vars(self):
        self.local_vars, self.global_vars = self.var_stack.pop()

    def make_block(self, stmts, indentation):
        indentstr = '  ' * indentation
        sep = '\n%s' % indentstr
        return '{\n%s%s\n%s}' % (indentstr, sep.join(stmts), '  ' * (indentation - 1))

    def make_func_block(self, stmts, indentation):
        indentstr = '  ' * indentation
        sep = '\n%s' % indentstr
        if self.local_vars:
            var = '%svar %s;\n%s' % (indentstr, ', '.join(sorted(self.local_vars)), indentstr)
        else:
            var = indentstr
        return '{\n%s%s\n%s}' % (var, sep.join(stmts), '  ' * (indentation - 1))

    def make_dict(self, items, indentation):
        indentstr = '  ' * indentation
        sep = ',\n%s' % indentstr
        return '{\n%s%s\n%s}' % (indentstr, sep.join(items), '  ' * (indentation - 1))

    def make_if(self, cond, block, elifexprs, elseblock):
        expr = ['if (%s) %s' % (cond, block)]
        expr.extend('else if (%s) %s' % x for x in elifexprs)
        if elseblock:
            expr.append('else %s' % elseblock)
        return ' '.join(expr)

    def make_for(self, var, data, body):
        indentstr = '  ' * self.indentation
        datavar = self.make_temp_var('data')
        lenvar = self.make_temp_var('len')
        index = self.make_temp_var('index')
        init = 'var %s = _$pyva_iter(%s);\n%svar %s = %s.length;\n%s' % (
            datavar, data, indentstr, lenvar, datavar, indentstr)
        body = body.replace('{', '{\n%s%s = %s[%s];\n' % (indentstr + '  ', var, datavar, index), 1)
        return '%sfor (var %s = 0; %s < %s; %s++) %s' % (init, index, index, lenvar, index, body)

    def temp_var_or_literal(self, name, var, init):
        """
        Returns either the literal if it's a literal or a temporary variable
        storing the non-literal in addition to regitering the temporary with
        init.
        """
        if var[0]:
            # Literal
            return var[1]
        temp = self.make_temp_var(name)
        init.append('%s = %s' % (temp, var[1]))
        return temp

    def make_for_range(self, var, for_range, body):
        # for_range is a list of tuples (bool:literal, str:js_code)
        indentstr = '  ' * self.indentation
        stepstr = '%s++' % var
        init = []
        if len(for_range) == 1:
            start = 0
            end = self.temp_var_or_literal('end', for_range[0], init)
        else:
            start = for_range[0][1]
            end = self.temp_var_or_literal('end', for_range[1], init)
            if len(for_range) == 3:
                step = self.temp_var_or_literal('step', for_range[2], init)
                stepstr = '%s += %s' % (var, step)

        initstr = ''
        if init:
            initstr = 'var %s;\n%s' % (', '.join(init), indentstr)

        return '%sfor (%s = %s; %s < %s; %s) %s' % (initstr, var, start, var,
                                                    end, stepstr, body)

    def make_for_reversed_range(self, var, for_range, body):
        indentstr = '  ' * self.indentation
        if len(for_range) == 1:
            return '%s = %s;\n%swhile (%s--) %s' % (var, for_range[0][1], indentstr, var, body)

        init = []
        start = for_range[1][1]
        end = self.temp_var_or_literal('end', for_range[0], init)
        if len(for_range) == 3:
            step = self.temp_var_or_literal('step', for_range[2], init)
            stepstr = '%s -= %s' % (var, step)
        else:
            stepstr = '%s--' % var

        initstr = ''
        if init:
            initstr = 'var %s;\n%s' % (', '.join(init), indentstr)

        return '%sfor (%s = (%s) - 1; %s >= %s; %s) %s' % (
            initstr, var, start, var, end, stepstr, body)

    def make_func(self, name, args, body):
        if name:
            self.register_var(name[1])
            func = '%s = function' % name[1]
        else:
            func = 'function'
        return '%s(%s) %s' % (func, ', '.join(args), body)
