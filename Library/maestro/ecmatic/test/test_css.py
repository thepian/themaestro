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
        def doIt(s):
            """
            @param s: The string to be parsed by the wrapped grammar.
            """
            obj = self.klass(s)
            ret, err = obj.apply(name)
            try:
                extra, _ = obj.input.head()
            except EOFError:
                try:
                    return ''.join(ret)
                except TypeError:
                    return ret
            else:
                raise err
        return doIt



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
