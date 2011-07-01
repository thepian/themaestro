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
    def test_in(self):
        self.check('x in y', '(x in y);')
        self.check('x not in y', '!(x in y);')

    def test_len(self):
        self.check('len(x)', 'x.length;')

    def test_dot(self):
        self.check('x.y.z', 'x.y.z;')

    def test_delete(self):
        self.check('del x[a]', 'delete x[a];')
        self.check("del x['a']", "delete x['a'];")
        self.check('del x.a', 'delete x.a;')

    def test_getitem(self):
        self.check('x[0]', 'x[0];')
        self.check('x[0][bla]', 'x[0][bla];')

    def test_negative_getitem_special(self):
        self.check('x[-1]', 'x.slice(-1)[0];')
        self.check('x[-2]', 'x.slice(-2, -1)[0];')

    def test_slicing(self):
        self.check('x[:]', 'x.slice(0);')
        self.check('x[3+3:]', 'x.slice((3 + 3));')
        self.check('x[3+3:]', 'x.slice((3 + 3));')
        self.check('x[:10]', 'x.slice(0, 10);')
        self.check('x[5:10]', 'x.slice(5, 10);')

    def test_hasattr(self):
        self.check('hasattr(x, y)', '(typeof x[y] != "undefined");')
        self.check('not hasattr(x, y)', '(typeof x[y] == "undefined");')

    def test_getattr(self):
        self.check('getattr(x, y)', 'x[y];')

    def test_setattr(self):
        self.check('setattr(x, y, z)', 'x[y] = z;')

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

    def test_return(self):
        self.check("""
        def():
            return
        """, """
        function() {
          return;
        }
        """)

        self.check("""
        def():
            return x
        """, """
        function() {
          return x;
        }
        """)

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

    def test_one_liners(self):
        self.check("""
        def f(): pass
        while True: pass
        for i in reversed(range(10)): pass
        """, """
        f = function() {
        };
        while (true) {
        }
        i = 10;
        while (i--) {
        }
        """)

    def test_multi_line_lambda(self):
        self.check("""
        x.prototype = {
            '__init__': def(self):
                def nested():
                    return None
                a = 3
                x = a + 3
                return x
            ,
            'add': def(self, a, b, c):
                return 1 + 2
            ,
        }
        """, """
        x.prototype = {
          '__init__': (function() {
            var a, nested, x;
            
            nested = function() {
              return null;
            };
            
            a = 3;
            x = (a + 3);
            return x;
          }),
          'add': (function(a, b, c) {
            return (1 + 2);
          })
        };
        """)

    def test_lambda_call(self):
        self.check("""
        (def():
            global x
            x = 5
        )()
        """, """
        (function() {
          x = 5;
        })();
        """)

    def test_self(self):
        self.check("""
        self.f()
        """, """
        self.f();
        """)

        self.check("""
        def f():
            self.f()
        """, """
        f = function() {
          self.f();
        };
        """)

        self.check("""
        def f(self):
            self.f()
        """, """
        f = function() {
          this.f();
        };
        """)

        self.check("""
        def f(self):
            myself = self
            def g():
                myself.f()
        """, """
        f = function() {
          var g, myself;
          myself = this;
          g = function() {
            myself.f();
          };
        };
        """)
