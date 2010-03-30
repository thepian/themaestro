#!/usr/bin/env python

"""
   Copyright 2010 Evgen Burzak

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

# PyJon: An ECMAScript implementation in Python

__author__ = "burzak"
__author_email__ = "buzzilo@gmail.com"
__date__ = "2009-10-27"

class FileNotFound(Exception): pass

import sys

if __name__ == "__main__":
    # Import Psyco if available
    try:
        pass 
        #import psyco
        #psyco.log()
        #psyco.profile()
        #psyco.full()
    except ImportError:
        sys.stderr.write("WARNING: psyco not loaded.\n"
                         "  To install: 'sudo apt-get install python-psyco'.\n"
                         "  Or visit http://psyco.sourceforge.net for additional info.\n")

import os, platform, subprocess, traceback
import jocore
from optparse import OptionParser

usage = "usage: %prog [options] project.yml"
parser = OptionParser(usage=usage, version="%prog " + repr(jocore.joos_version), add_help_option=False)
parser.set_defaults(verbose=True)
parser.add_option("-h", "--help", action="help",
                  help="show this help message and exit")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet", default=False,
                  help="mute all output")
parser.add_option("-r", "--run", action="store_true", dest="run", default=False,
                  help="run the code [default]")
parser.add_option("", "--js-shell",
                  dest="command", default="v8 -e",
                  help="DEPRECATED. command to use as javascript shell [default: %default]")
parser.add_option("-o", "--compile",
                  metavar="FILE", dest="compile", default=False,
                  help="compile the code into executable package")
parser.add_option("-s", "", dest="script", action="append", type="string", help="input script")
parser.add_option("-2", "", dest="as2_script", action="append", type="string", help="")
parser.add_option("-3", "", dest="as3_script", action="append", type="string", help="")
parser.add_option("", "--shell", dest="console", action="store_true", default=False,
                  help="run an interactive shell")
parser.add_option("-a", "--asset", dest="assets", action="append",
                    metavar="FILE", 
                    help="including FILE in compilation")
parser.add_option("-L", "--lib", dest="lib_path", action="append",
                    help="add directory LIB_PATH to the list of directories to "
                         "be searched for importing [default: %s]" % ", ".join(jocore.libs))
parser.add_option("-l", "--link", dest="link", action="append",
                    metavar="CLASS_NS",
                    help="link with CLASS_NS (do not store code in the compilation)")
parser.add_option("", "--optimize", dest="ACTION", default="minify",
                    help="optimization level [default: %default]")
"""
parser.add_option("", "--strict", action="store_true", dest="strict_mode", default=False,
                  help="treat strict errors as fatal")
parser.add_option("", "--strict-typing", action="store_false", dest="strict_typing", default=False,
                  help="treat type errors as fatal")
parser.add_option("", "--soft-typing", action="store_true", dest="strict_typing", default=True,
                  help="treat type errors as warnings [default]")
parser.add_option("", "--runtime-typing", action="store_true", dest="dynamic_typing", default=False,
                  help="check types at the runtime")
parser.add_option("", "--no-class-signing", action="store_true", dest="no_class_signing", default=False,
                    help="skip class signing. WARNING: may produce inconsistent code!")
"""
parser.add_option("", "--disable-runtime-typing", action="store_true", dest="dynamic_typing", default=False)
parser.add_option("-d", "--debug", type="int", dest="debug_level", default=0,
                    help="debug level 1..3 (last one make lots of noise)")


def IsWindows():
  p = platform.system()
  return (p == 'Windows') or (p == 'Microsoft')

def main(argv):

    (options, args) = parser.parse_args()
    """
    if not len(args) and not options.console: 
        parser.error("please specify at least one script name or project config")
        return 1
    """

    command = options.command

    if options.lib_path:
        jocore.libs.extend(options.lib_path)

    jocore.debug = options.debug_level

    i = 1

    args.reverse()
    try:
        for script in args:
            if not os.path.isfile(script):
                raise FileNotFound, script + " not found"
            #jocore.convert(script, root, i*100)
            jocore.load(script)
            i += 1
        if options.console or not len(args):
            print "pyjon, v%s" % str(jocore.__version__)
            con = jocore.shell()
            while True:
                try:
                    input = raw_input("> ")
                    out = con.eval(input)
                    if out == None: pass
                    else: print out
                except (EOFError, KeyboardInterrupt):
                    print
                    return 0
                except Exception, e:
                    print e.__class__.__name__ + ": " + str(e.message)
                    if options.debug_level > 1: traceback.print_exc(file=sys.stderr)

    except Exception, e:
        if len(args):
            print "Failure in converting %s to JavaScript" % (args[i-1])
        print e.__class__.__name__ + ": " + str(e.message)
        if options.debug_level > 1: traceback.print_exc(file=sys.stderr)
        return 1

    return 0

    compiled = jocore.compile()

    if options.compile: print compiled

    if (options.translate and options.run) or \
            (not options.translate):
        if IsWindows():
          args = '"%s %s"' % (command, compiled)
        else:
          args = command.split(" ")
          args.append(compiled)

        #stdout = out
        #stderr = err
        try:
            #print "exec: %s" % str(args)
            process = subprocess.Popen(
                args,
                shell = IsWindows()
                #stdout = stdout.fd,
                #stderr = stderr.fd
            )
            code = process.wait()
            #out = stdout.Read()
            #err = stderr.Read()
        except NameError:
            raise
        #finally:
            #stdout.Dispose()
            #stderr.Dispose()

    sys.stdout.flush()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
