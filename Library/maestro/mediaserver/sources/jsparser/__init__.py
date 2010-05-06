#!/usr/bin/python2.5
# -*- coding: utf-8 -*-

# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is the Narcissus JavaScript engine, written in Javascript.
#
# The Initial Developer of the Original Code is
# Brendan Eich <brendan@mozilla.org>.
# Portions created by the Initial Developer are Copyright (C) 2004
# the Initial Developer. All Rights Reserved.
#
# The Python version of the code was created by JT Olds <jtolds@xnet5.com>,
# and is a direct translation from the Javascript version.
#
# <Burzak was here>, he improves the code a little bit.
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK ***** */
#
# TODO 
#
#     >>> function range(begin, end) {
#           for (let i = begin; i < end; ++i) {
#             yield i;
#           }
#         }
#         var gen = [i for each (i in range(0, 21)) if (i % 2 == 0)]; 
#
# FIXME notice: in ECMAScript 5 'with' statement is deprecated, but not in Joo.
#       You could convert your script into jooscript. Thus 'with' statements
#       will be translated via functions without execution speed affected.
#
# TODO  1. extend Node for every entity. 
#       2. Store node attributes as list values to make possible serializing nodes in array.
  

"""
 Joo/Java/ActionScript Parser (formed PyNarcissus)

 A lexical scanner and parser. JS implemented in JS, ported to Python, extended with new syntax. <- revert
"""

__author__ = "JT Olds"
__author_email__ = "jtolds@xnet5.com"
__date__ = "2009-03-24"

__author__ = "buzz"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2009-09-15"

__all__ = ["ParseError", "parse", "tokens"]

import os, re, sys, types, struct, string, copy
import md5

hash_ = md5
"""
try:
    import crcmod
    g32 = 0x104C11DB7
    hash_ = crcmod.Crc(g32)
except ImportError:
    hash_ = md5
"""

class Object: pass
class Error_(Exception): pass
class ParseError(Error_): pass
class WTF(Exception): pass


def parse(source, source_context=None, starting_line_number=1, strictMode=False, 
        import_order = 0, depth = 1, glob = None):
    """Parse some Javascript

    Args:
        source_context: information about the script file/url
        source: the Javascript source, as a string
        starting_line_number: the line number of the first line of the
            passed in source, for output messages
    Returns:
        the parsed source code data structure
    Raises:
        ParseError
    """
    if source_context:
        path = source_context.path
        filename = source_context.script_name
        script_type = source_context.script_type
        ns = source_context.namespace
        root_scope = source_context.root_scope 
        strictMode = source_context.strictMode
    else:
        path = None
        filename = None
        script_type = "javascript"
        ns = None
        root_scope = None
        strictMode = None

     #path="", filename="", script_type="jooscript", ns=None, 
        #import_order=0, depth=1, root_scope=None,

    # Init(source_context, script_type, glob or globals())
    t = Tokenizer(source, path, filename, ns, starting_line_number)
    x = CompilerContext(script_type == "class" and PACKAGE or MODULE, 
            import_order = import_order, depth = depth-1, root_scope = root_scope,
            strictMode = strictMode)
    n = Script(t, x)
    if script_type == "class":
        ValidatePackage(t,x,True)

    if not t.done:
        raise t.newSyntaxError("Syntax error")
    return n

if __name__ == "__main__":
    print str(parse(file(sys.argv[1]).read(),sys.argv[1]))
