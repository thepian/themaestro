from pymeta.builder import TreeBuilder, moduleFromGrammar
from pymeta.grammar import OMetaGrammar
from pymeta.runtime import _MaybeParseError, OMetaBase, EOFError, expected
from textwrap import dedent
import unittest

class HandyWrapper(object):
    """
    Convenient grammar wrapper for parsing strings.
    """
    def __init__(self, klass):
        """
        @param klass: The grammar class to be wrapped.
        """
        self.klass = klass


    def __getattr__(self, name):
        """
        Return a function that will instantiate a grammar and invoke the named
        rule.
        @param: Rule name.
        """
        def doIt(s,matchAll=True):
            """
            @param s: The string to be parsed by the wrapped grammar.
            """
            obj = self.klass(s)
            ret, err = obj.apply(name)
            if not matchAll:
                if type(ret) is type({}):
                    return ret
                try:
                    return ''.join(ret)
                except TypeError:
                    return ret
            try:
                extra, _ = obj.input.head()
            except EOFError:
                if type(ret) is type({}):
                    return ret
                try:
                    return ''.join(ret)
                except TypeError:
                    return ret
            else:
                print 'Additional stuff present', extra
                raise err
        return doIt



class OMetaTestCase(unittest.TestCase):
    """
    Tests of OMeta grammar compilation.
    """

    classTested = OMetaGrammar

    def compile(self, grammar):
        """
        Produce an object capable of parsing via this grammar.

        @param grammar: A string containing an OMeta grammar.
        """
        g = self.classTested(dedent(grammar))
        tree = g.parseGrammar('TestGrammar', TreeBuilder)
        result = moduleFromGrammar(tree, 'TestGrammar', OMetaBase, {})
        return HandyWrapper(result)



    def test_literals(self):
        """
        Input matches can be made on literal characters.
        """
        g = self.compile("digit = '1'")
        self.assertEqual(g.digit("1"), "1")
        self.assertRaises(_MaybeParseError, g.digit, "4")
        
        g = self.compile("space = ' '")
        self.assertEqual(g.space(" "), " ")
        self.assertRaises(_MaybeParseError, g.space, ".")

    def test_named_literals(self):
        """
        Input matches can be made on named literal characters.
        """
        g = self.compile("""
space = '{SP}' | '{nbsp}'
nul = '{NUL}'      
tab = '{HT}'  
whitespace ('{SP}' | '{nbsp}' | '{HT}' | '{VT}')+
lines = ((('{CR}':r '{LF}':n) -> r+n) | '{CR}' | '{LF}' )+
spaces_or_comments = (space | "/**/")+
crcr = '{CR}' '{CR}' -> "\r\r"
        """)
        self.assertEqual(g.nul("\0"), "\0")
        self.assertEqual(g.space(" "), " ")
        self.assertEqual(g.space(u"\xA0"), u"\xA0")
        self.assertEqual(g.tab("\t"), "\t")
        self.assertEqual(g.whitespace(u" \t \xA0\v"), u" \t \xA0\v")
        self.assertEqual(g.lines(u"\n\r"),u"\n\r")
        self.assertEqual(g.spaces_or_comments(u"/**/ "), u"/**/ ")
        self.assertRaises(_MaybeParseError, g.space, ".")
        
        ret, err = g.klass(u" \t \xA0").apply("whitespace")
        assert ret == [u" ",u"\t",u" ",u"\xA0"]

        ret, err = g.klass(u" /**/").apply("spaces_or_comments")
        assert ret == [u" ",u"/**/"]

        ret, err = g.klass(u"\r\n\n\r").apply("lines")
        assert ret == [u"\r\n", u"\n",u"\r"]
        
        ret, err = g.klass(u"\r\r").apply("crcr")
        assert ret == u"\r\r"


    def test_multipleRules(self):
        """
        Grammars with more than one rule work properly.
        """
        g = self.compile("""
                          digit = '1'
                          aLetter = 'a'
                          """)
        self.assertEqual(g.digit("1"), "1")
        self.assertRaises(_MaybeParseError, g.digit, "4")


    def test_escapedLiterals(self):
        """
        Input matches can be made on escaped literal characters.
        """
        g = self.compile(r"newline = '\n'")
        self.assertEqual(g.newline("\n"), "\n")


    def test_integers(self):
        """
        Input matches can be made on literal integers.
        """
        g = self.compile("stuff = 17 0x1F -2 0177")
        self.assertEqual(g.stuff([17, 0x1f, -2, 0177]), 0177)
        self.assertRaises(_MaybeParseError, g.stuff, [1, 2, 3])


    def test_star(self):
        """
        Input matches can be made on zero or more repetitions of a pattern.
        """
        g = self.compile("xs = 'x'*")
        self.assertEqual(g.xs(""), "")
        self.assertEqual(g.xs("x"), "x")
        self.assertEqual(g.xs("xxxx"), "xxxx")
        self.assertRaises(_MaybeParseError, g.xs, "xy")


    def test_plus(self):
        """
        Input matches can be made on one or more repetitions of a pattern.
        """
        g = self.compile("xs = 'x'+")
        self.assertEqual(g.xs("x"), "x")
        self.assertEqual(g.xs("xxxx"), "xxxx")
        self.assertRaises(_MaybeParseError, g.xs, "xy")
        self.assertRaises(_MaybeParseError, g.xs, "")


    def test_sequencing(self):
        """
        Input matches can be made on a sequence of patterns.
        """
        g = self.compile("twelve = '1' '2'")
        self.assertEqual(g.twelve("12"), "2");
        self.assertRaises(_MaybeParseError, g.twelve, "1")


    # def test_combines(self):
    #     """
    #     Input matches can be made on a sequence of patterns, combining the match as a result.
    #     """
    #     g = self.compile("twelve = '1' & '2'")
    #     self.assertEqual(g.twelve("12"), "12");
    #     self.assertRaises(_MaybeParseError, g.twelve, "1")


    def test_alternatives(self):
        """
        Input matches can be made on one of a set of alternatives.
        """
        g = self.compile("digit = '0' | '1' | '2'")
        self.assertEqual(g.digit("0"), "0")
        self.assertEqual(g.digit("1"), "1")
        self.assertEqual(g.digit("2"), "2")
        self.assertRaises(_MaybeParseError, g.digit, "3")


    def test_optional(self):
        """
        Subpatterns can be made optional.
        """
        g = self.compile("foo = 'x' 'y'? 'z'")
        self.assertEqual(g.foo("xyz"), 'z')
        self.assertEqual(g.foo("xz"), 'z')


    def test_apply(self):
        """
        Other productions can be invoked from within a production.
        """
        g = self.compile("""
              digit = '0' | '1'
              bits = digit+
            """)
        self.assertEqual(g.bits('0110110'), '0110110')


    def test_negate(self):
        """
        Input can be matched based on its failure to match a pattern.
        """
        g = self.compile("foo = ~'0' anything")
        self.assertEqual(g.foo("1"), "1")
        self.assertRaises(_MaybeParseError, g.foo, "0")


    def test_ruleValue(self):
        """
        Productions can specify a Python expression that provides the result
        of the parse.
        """
        g = self.compile("foo = '1' -> 7")
        self.assertEqual(g.foo('1'), 7)


    def test_lookahead(self):
        """
        Doubled negation does lookahead.
        """
        g = self.compile("""
                         foo = ~~(:x) bar(x)
                         bar :x = :a :b ?(x == a == b) -> x
                         """)
        self.assertEqual(g.foo("11"), '1')
        self.assertEqual(g.foo("22"), '2')


    def test_binding(self):
        """
        The result of a parsing expression can be bound to a name.
        """
        g = self.compile("foo = '1':x -> int(x) * 2")
        self.assertEqual(g.foo("1"), 2)


    def test_bindingAccess(self):
        """
        Bound names in a rule can be accessed on the grammar's "locals" dict.
        """
        gg = self.classTested("stuff = '1':a ('2':b | '3':c)")
        t = gg.parseGrammar('TestGrammar', TreeBuilder)
        G = moduleFromGrammar(t, 'TestGrammar', OMetaBase, {})
        g = G("12")
        self.assertEqual(g.apply("stuff")[0], '2')
        self.assertEqual(g.locals['stuff']['a'], '1')
        self.assertEqual(g.locals['stuff']['b'], '2')
        g = G("13")
        self.assertEqual(g.apply("stuff")[0], '3')
        self.assertEqual(g.locals['stuff']['a'], '1')
        self.assertEqual(g.locals['stuff']['c'], '3')


    def test_predicate(self):
        """
        Python expressions can be used to determine the success or failure of a
        parse.
        """
        g = self.compile("""
              digit = '0' | '1'
              double_bits = digit:a digit:b ?(a == b) -> int(b)
           """)
        self.assertEqual(g.double_bits("00"), 0)
        self.assertEqual(g.double_bits("11"), 1)
        self.assertRaises(_MaybeParseError, g.double_bits, "10")
        self.assertRaises(_MaybeParseError, g.double_bits, "01")


    def test_parens(self):
        """
        Parens can be used to group subpatterns.
        """
        g = self.compile("foo = 'a' ('b' | 'c')")
        self.assertEqual(g.foo("ab"), "b")
        self.assertEqual(g.foo("ac"), "c")


    def test_action(self):
        """
        Python expressions can be run as actions with no effect on the result
        of the parse.
        """
        g = self.compile("""foo = ('1'*:ones !(False) !(ones.insert(0, '0')) -> ''.join(ones))""")
        self.assertEqual(g.foo("111"), "0111")


    def test_bindNameOnly(self):
        """
        A pattern consisting of only a bind name matches a single element and
        binds it to that name.
        """
        g = self.compile("foo = '1' :x '2' -> x")
        self.assertEqual(g.foo("132"), "3")

        
    def test_bindAnyting(self):
        """
        A pattern consisting of anything and a bind name matches a single element and
        binds it to that name.
        """
        g = self.compile("foo = '1' anything:x '2' -> x")
        self.assertEqual(g.foo("132"), "3")


#     def test_many(self):
#         g = self.compile("""
# bar = '1' | '2' | '3'
# foo = many(self.rule_bar):x -> x
# """)
#         self.assertEqual(g.foo("132"), "3")
# 
        
    def test_keyword(self):
        g = self.compile("""
keyword_letter = letterOrDigit | '{nbsp}' | '{zwj}'
keyword_prefix = ' '
foo132 = keyword("f132")
foo133 = keyword("f133")
foo13 = foo132 | foo133
foozw = keyword('z','{zwj}','w')
foonb = keyword('n',u'\xA0','b')
""")
        self.assertEqual(g.foo132(u"f132"), { 'keyword':u"f132", 'prefix':[] })
        self.assertEqual(g.foo132(u"f132 ",matchAll=False), { 'keyword':u"f132", 'prefix':[] })
        self.assertEqual(g.foo132(u"f132(1)",matchAll=False), { 'keyword':u"f132", 'prefix':[] })
        self.assertEqual(g.foo133(u"f133(1)",matchAll=False), { 'keyword':u"f133", 'prefix':[] })
        self.assertEqual(g.foo13(u"f133(1)",matchAll=False), { 'keyword':u"f133", 'prefix':[] })
        self.assertRaises(_MaybeParseError, g.foo132, u"f1324")
        self.assertEqual(g.keyword_letter(u"\xA0"),u"\xA0")
        self.assertRaises(_MaybeParseError, g.foo132, u"f132\xA04")
        self.assertRaises(_MaybeParseError, g.foo132, u"f124")
        self.assertEqual(g.foo132(u" f132"), { 'keyword':u"f132", 'prefix':[" "] })

        from htmlentitydefs import entitydefs
        # self.assertEqual(g.foozw(u"z" + (entitydefs['zwj']) + u"w"), u"z" + (entitydefs['zwj']) + u"w")
        # self.assertEqual(g.foonb("n\xA0b"), "n\xA0b")
        # self.assertEquals(g.)

    #TODO multi letter character literals only allowed for named chars

    def test_binary(self):
        g = self.compile("""
hspace = ' ' | '{HT}'
comment = "/**/"

name = letterOrDigit+:l -> ''.join(l)

k_postfix = (hspace | comment)*
keyword_prefix = hspace | comment
instanceof_apply = apply("keyword","instanceof")
instanceof_k = keyword("instanceof")

instanceof = name:a keyword("instanceof"):k k_postfix:postfix name:b -> ["instanceof",{ 'prefix':k['prefix'], 'postfix':postfix }, a, b]
""")
        # the apply is called as apply( ("keyword","instanceof") ), TODO find out how to do parameterized apply
        # self.assertEqual(g.instanceof_apply( "instanceof"), {'keyword':"instanceof", 'prefix':[]})
        # self.assertEqual(g.instanceof_apply( "/**/ instanceof"), {'keyword':"instanceof", 'prefix':[ "/**/", " " ]})
        self.assertEqual(g.instanceof_k( "instanceof"), {'keyword':"instanceof", 'prefix':[]})
        self.assertEqual(g.instanceof_k( "/**/ instanceof"), {'keyword':"instanceof", 'prefix':[ "/**/", " " ]})

        self.assertRaises(_MaybeParseError, g.instanceof_k, u"instanceof2")
        self.assertRaises(_MaybeParseError, g.instanceof_k, u" /**/ \tinstanceof2")
        self.assertRaises(_MaybeParseError, g.instanceof_k, u"instance")
        # self.assertEqual(g.instanceof_k( "instanceof2"), {'keyword':"instanceof", 'prefix':[]})

        self.assertEqual(g.instanceof( "a instanceof b"), ["instanceof", {'prefix':[" "], 'postfix':[" "]}, "a", "b" ])
        
    def test_symbol(self):
        g = self.compile("""
token_lead = ' '
less = token("<")
more = token(">")
""")
        self.assertEqual(g.less(u"<"), u"<")
        self.assertEqual(g.less(u"< ",matchAll=False), u"<")
        self.assertEqual(g.less(u" <(1)",matchAll=False), u"<")
        self.assertEqual(g.more(u">(1)",matchAll=False), u">")

        
    def test_args(self):
        """
        Productions can take arguments.
        """
        g = self.compile("""
              digit = ('0' | '1' | '2'):d -> int(d)
              foo :x = (?(x > 1) '9' | ?(x <= 1) '8'):d -> int(d)
              baz = digit:a foo(a):b -> [a, b]
            """)
        self.assertEqual(g.baz("18"), [1, 8])
        self.assertEqual(g.baz("08"), [0, 8])
        self.assertEqual(g.baz("29"), [2, 9])
        self.assertRaises(_MaybeParseError, g.foo, "28")


    def test_patternMatch(self):
        """
        Productions can pattern-match on arguments.
        Also, multiple definitions of a rule can be done in sequence.
        """
        g = self.compile("""
              fact 0                       -> 1
              fact :n = fact((n - 1)):m -> n * m
           """)
        self.assertEqual(g.fact([3]), 6)


    def test_apply_rule(self):
        """
        Productions can pattern-match on arguments even if they're lists.
        """
        g = self.compile("""
              fact 0                    -> 1
              fact :n = fact((n - 1)):m -> n * m
              domany = interp*
              interp = [:name apply(name):x] -> x
           """)
        self.assertEqual(g.interp([['domany', ['fact', 3], ['fact', 5]]]),
                         [6, 120])


    def test_listpattern(self):
        """
        Brackets can be used to match contents of lists.
        """
        g = self.compile("""
             digit  = :x ?(x.isdigit())          -> int(x)
             interp = [digit:x '+' digit:y] -> x + y
           """)
        self.assertEqual(g.interp([['3', '+', '5']]), 8)

    def test_listpatternresult(self):
        """
        The result of a list pattern is the entire list.
        """
        g = self.compile("""
             digit  = :x ?(x.isdigit())          -> int(x)
             interp = [digit:x '+' digit:y]:z -> (z, x + y)
        """)
        e = ['3', '+', '5']
        self.assertEqual(g.interp([e]), (e, 8))

    def test_recursion(self):
        """
        Rules can call themselves.
        """
        g = self.compile("""
             interp = (['+' interp:x interp:y] -> x + y
                       | ['*' interp:x interp:y] -> x * y
                       | :x ?(isinstance(x, str) and x.isdigit()) -> int(x))
             """)
        self.assertEqual(g.interp([['+', '3', ['*', '5', '2']]]), 13)


    def test_leftrecursion(self):
         """
         Left-recursion is detected and compiled appropriately.
         """
         g = self.compile("""
               num = (num:n digit:d   -> n * 10 + d
                      | digit)
               digit = :x ?(x.isdigit()) -> int(x)
              """)
         self.assertEqual(g.num("3"), 3)
         self.assertEqual(g.num("32767"), 32767)


    def test_characterVsSequence(self):
        """
        Characters (in single-quotes) are not regarded as sequences.
        """
        g = self.compile("""
        interp = ([interp:x '+' interp:y] -> x + y
                  | [interp:x '*' interp:y] -> x * y
                  | :x ?(isinstance(x, basestring) and x.isdigit()) -> int(x))
        """)
        self.assertEqual(g.interp([['3', '+', ['5', '*', '2']]]), 13)
        self.assertEqual(g.interp([[u'3', u'+', [u'5', u'*', u'2']]]), 13)


    def test_string_object(self):
        """
        Strings in double quotes match string objects.
        """
        g = self.compile("""
             interp = ['Foo' 1 2] -> 3
           """)
        self.assertEqual(g.interp([["Foo", 1, 2]]), 3)

    def test_match_string(self):
        """
        Strings in double quotes match string objects.
        """
        g = self.compile("""
             interp = "Foo" 1 2 -> 3
           """)
        self.assertEqual(g.interp(['F', 'o', 'o', 1, 2]), 3)
        
    def test_allow_comments(self):
        """
        Full line comments before a rule is allowed
        """
        g = self.compile("""
            # comment for interp
            interp = "Foo" 1 2 -> 3
            """)
        self.assertEqual(g.interp(['F', 'o', 'o', 1, 2]), 3)

        g = self.compile("""
            // comment for interp
            interp = "Foo" 1 2 -> 3
            """)
        self.assertEqual(g.interp(['F', 'o', 'o', 1, 2]), 3)

    def test_argEscape(self):
        """
        Regression test for bug #239344.
        """
        g = self.compile("""
            memo_arg :arg = anything ?(False)
            trick = letter memo_arg('c')
            broken = trick | anything*
        """)
        self.assertEqual(g.broken('ab'), 'ab')



class PyExtractorTest(unittest.TestCase):
    """
    Tests for finding Python expressions in OMeta grammars.
    """

    def findInGrammar(self, expr):
        """
        L{OMeta.pythonExpr()} can extract a single Python expression from a
        string, ignoring the text following it.
        """
        o = OMetaBase(expr + "\nbaz = ...\n")
        self.assertEqual(o.pythonExpr()[0][0], expr)


    def test_expressions(self):
        """
        L{OMeta.pythonExpr()} can recognize various paired delimiters properly
        and include newlines in expressions where appropriate.
        """
        self.findInGrammar("x")
        self.findInGrammar("(x + 1)")
        self.findInGrammar("{x: (y)}")
        self.findInGrammar("x, '('")
        self.findInGrammar('x, "("')
        self.findInGrammar('x, """("""')
        self.findInGrammar('(x +\n 1)')
        self.findInGrammar('[x, "]",\n 1]')
        self.findInGrammar('{x: "]",\ny: "["}')

        o = OMetaBase("foo(x[1]])\nbaz = ...\n")
        self.assertRaises(_MaybeParseError, o.pythonExpr)
        o = OMetaBase("foo(x[1]\nbaz = ...\n")
        self.assertRaises(_MaybeParseError, o.pythonExpr)


class MakeGrammarTest(unittest.TestCase):
    """
    Test the definition of grammars via the 'makeGrammar' method.
    """


    def test_makeGrammar(self):
        #imported here to prevent OMetaGrammar from being constructed before
        #tests are run
        from pymeta.grammar import OMeta
        results = []
        grammar = dedent("""
        digit = :x ?('0' <= x <= '9') -> int(x)
        num = (num:n digit:d !(results.append(True)) -> n * 10 + d
               | digit)
        """)
        TestGrammar = OMeta.makeGrammar(grammar, {'results':results})
        g = TestGrammar("314159")
        self.assertEqual(g.apply("num")[0], 314159)
        self.assertNotEqual(len(results), 0)


    def test_subclassing(self):
        """
        A subclass of an OMeta subclass should be able to call rules on its
        parent.
        """
        from pymeta.grammar import OMeta

        grammar1 = dedent("""
        dig = :x ?('0' <= x <= '9') -> int(x)
        """)
        TestGrammar1 = OMeta.makeGrammar(grammar1, {})

        grammar2 = dedent("""
        num = (num:n dig:d -> n * 10 + d
                | dig)
        """)
        TestGrammar2 = TestGrammar1.makeGrammar(grammar2, {})
        g = TestGrammar2("314159")
        self.assertEqual(g.apply("num")[0], 314159)


    def test_super(self):
        """
        Rules can call the implementation in a superclass.
        """
        from pymeta.grammar import OMeta
        grammar1 = "expr = letter"
        TestGrammar1 = OMeta.makeGrammar(grammar1, {})
        grammar2 = "expr = super | digit"
        TestGrammar2 = TestGrammar1.makeGrammar(grammar2, {})
        self.assertEqual(TestGrammar2("x").apply("expr")[0], "x")
        self.assertEqual(TestGrammar2("3").apply("expr")[0], "3")
        
    def test_allow_comments(self):
        """
        Full line comments before a rule is allowed
        Make sure that the boot.py version supports comments
        """
        from pymeta.grammar import OMeta
        g = OMeta.makeGrammar("""
# comment for interp
interp = "Foo" 1 2 -> 3
            """,{})
        self.assertEqual(g(['F', 'o', 'o', 1, 2]).apply("interp")[0], 3)

        g = OMeta.makeGrammar("""
// comment for interp
interp = "Foo" 1 2 -> 3
            """,{})
        self.assertEqual(g(['F', 'o', 'o', 1, 2]).apply("interp")[0], 3)

    

class SelfHostingTest(OMetaTestCase):
    """
    Tests for the OMeta grammar parser defined with OMeta.
    """
    classTested = None


    def setUp(self):
        """
        Run the OMeta tests with the self-hosted grammar instead of the boot
        one.
        """
        #imported here to prevent OMetaGrammar from being constructed before
        #tests are run
        if self.classTested is None:
            from pymeta.grammar import OMetaGrammar
            self.classTested = OMetaGrammar
                        



class NullOptimizerTest(OMetaTestCase):
    """
    Tests of OMeta grammar compilation via the null optimizer.
    """

    def compile(self, grammar):
        """
        Produce an object capable of parsing via this grammar.

        @param grammar: A string containing an OMeta grammar.
        """
        from pymeta.grammar import OMetaGrammar, NullOptimizer
        g = OMetaGrammar(dedent(grammar))
        tree  = g.parseGrammar('TestGrammar', TreeBuilder)
        opt = NullOptimizer([tree])
        opt.builder = TreeBuilder("TestGrammar", opt)
        tree, err = opt.apply("grammar")
        grammarClass = moduleFromGrammar(tree, 'TestGrammar', OMetaBase, {})
        return HandyWrapper(grammarClass)
