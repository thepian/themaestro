__author__ = 'henrikvendelbo'

from unittest import TestCase
from ecmatic.basic import compile
from textwrap import dedent

class PyvaTest(TestCase):
    def check(self, source, result):
        source = '\n'.join(line for line in
                           dedent(compile(dedent(source))).strip().splitlines()
                           if line)
        result = '\n'.join(line for line in dedent(result).strip().splitlines()
                           if line)
        try:
            self.assertEqual(source, result)
        except:
            raise AssertionError('\n%s\n!=\n%s' % (repr(source), repr(result)))

class Test(PyvaTest):
    def test_dot(self):
        self.check('x.y.z', 'x.y.z;')

    def test_if(self):
        self.check("""
        if ((((a == 3) || ((b === null) && (c == true))) || (d != false))) {
          f();
        }
        """, """
        if ((((a == 3) || ((b === null) && (c == true))) || (d != false))) {
          f();
        }
        """)

