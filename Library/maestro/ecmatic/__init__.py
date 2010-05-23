from __future__ import with_statement
from javascript15 import Tokenizer, CompilerContext, Script

def parse(source, filename=None, starting_line_number=1, language="Javascript1.5"):
    """Parse some Javascript

    Args:
        source: the Javascript source, as a string
        filename: the filename to include in messages
        starting_line_number: the line number of the first line of the
            passed in source, for output messages
    Returns:
        the parsed source code data structure
    Raises:
        ParseError
    """
    t = Tokenizer(source, filename, starting_line_number)
    x = CompilerContext(False)
    n = Script(t, x)
    if not t.done:
        raise t.newSyntaxError("Syntax error")
    return n

if __name__ == "__main__":
    with open(sys.argv[1],"r") as f:
        print str(parse(f.read(),sys.argv[1]))
