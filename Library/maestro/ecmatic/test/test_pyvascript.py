__author__ = 'henrikvendelbo'

from unittest import TestCase
from ecmatic.pyvascript import compile
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

    def test_getitem(self):
        self.check('x[0]', 'x[0];')
        self.check('x[0][bla]', 'x[0][bla];')

    def test_dot_getitem(self):
        self.check('x.y[0]', 'x.y[0];')
        self.check('x.y[0].z', 'x.y[0].z;')
        self.check('x.y[0].z[214]', 'x.y[0].z[214];')

    def test_call_dot_getitem(self):
        self.check('x.f().y[0]', 'x.f().y[0];')
        self.check('x.y[0].z()', 'x.y[0].z();')
        self.check('x.y[0].z[214].f().a', 'x.y[0].z[214].f().a;')

    def test_assign_call_dot_getitem(self):
        self.check('a = x.f().y[0]', 'a = x.f().y[0];')
        self.check('a = x.y[0].z()', 'a = x.y[0].z();')
        self.check('a = x.y[0].z[214].f().a', 'a = x.y[0].z[214].f().a;')
        self.check('a += x.y[0].z[214].f().a', 'a += x.y[0].z[214].f().a;')

    def test_if(self):
        self.check("""
        if a == 3 or b is None and c == True or d != False:
            f()
        """, """
        if ((((a == 3) || ((b === null) && (c == true))) || (d != false))) {
          f();
        }
        """)

    def test_while(self):
        self.check("""
        while a == 3 or b is None and c == True or d != False:
            f()
            if x:
                break
            continue
        """, """
        while ((((a == 3) || ((b === null) && (c == true))) || (d != false))) {
          f();
          if (x) {
            break;
          }

          continue;
        }
        """)

    def test_for_range_literal(self):
        self.check("""
        for i in range(10):
            f()
        """, """
        for (i = 0; i < 10; i++) {
          f();
        }
        """)

        self.check("""
        for i in range(2, 10):
            f()
        """, """
        for (i = 2; i < 10; i++) {
          f();
        }
        """)

        self.check("""
        for i in range(2, 10, 2):
            f()
        """, """
        for (i = 2; i < 10; i += 2) {
          f();
        }
        """)

    def test_for_range_nonliteral(self):
        self.check("""
        for i in range(x(10)):
            f()
        """, """
        var _$tmp1_end = x(10);
        for (i = 0; i < _$tmp1_end; i++) {
          f();
        }
        """)

        self.check("""
        for i in range(x(2), x(10)):
            f()
        """, """
        var _$tmp1_end = x(10);
        for (i = x(2); i < _$tmp1_end; i++) {
          f();
        }
        """)

        self.check("""
        for i in range(x(2), x(10), x(2)):
            f()
        """, """
        var _$tmp1_end = x(10), _$tmp2_step = x(2);
        for (i = x(2); i < _$tmp1_end; i += _$tmp2_step) {
          f();
        }
        """)

    def test_for_reversed_range_literal(self):
        self.check("""
        for i in reversed(range(2, 10)):
            f()
        """, """
        for (i = (10) - 1; i >= 2; i--) {
          f();
        }
        """)

        self.check("""
        for i in reversed(range(2, 10, 2)):
            f()
        """, """
        for (i = (10) - 1; i >= 2; i -= 2) {
          f();
        }
        """)

    def test_for_reversed_range_nonliteral(self):
        self.check("""
        for i in reversed(range(x(10))):
            f()
        """, """
        i = x(10);
        while (i--) {
          f();
        }
        """)

        self.check("""
        for i in reversed(range(x(2), x(10))):
            f()
        """, """
        var _$tmp1_end = x(2);
        for (i = (x(10)) - 1; i >= _$tmp1_end; i--) {
          f();
        }
        """)

        self.check("""
        for i in reversed(range(x(2), x(10), x(2))):
            f()
        """, """
        var _$tmp1_end = x(2), _$tmp2_step = x(2);
        for (i = (x(10)) - 1; i >= _$tmp1_end; i -= _$tmp2_step) {
          f();
        }
        """)

    def test_for_in(self):
        self.check("""
        for i in x.y[10].z():
            f(i)
        """, """
        var _$tmp1_data = _$pyva_iter(x.y[10].z());
        var _$tmp2_len = _$tmp1_data.length;
        for (var _$tmp3_index = 0; _$tmp3_index < _$tmp2_len; _$tmp3_index++) {
          i = _$tmp1_data[_$tmp3_index];

          f(i);
        }
        """)

    def test_multi_line_lambda(self):
        self.check("""
        x.prototype = {
            '__init__':
            def(self):
                def nested():
                    return None
                a = 3
                x = a + 3
                return x
            ,
            'add':
            def(self, a, b, c):
                return 1 + 2
            ,
        }
        """, """
        x.prototype = {
          "__init__": function(self) {
            var a, nested, x;

            nested = function() {
              return null;
            }

            a = 3;
            x = (a + 3);
            return x;
          },
          "add": function(self, a, b, c) {
            return (1 + 2);
          }
        };
        """)
