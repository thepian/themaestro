from ecmatic import parse

def test_blank():
    res = parse("")
    assert str(res) == ""
    
def no_test_function_def():
    snippet = """
function f() { 
    return 0; 
}
"""
    res = parse(snippet)
    assert str(res) == snippet+"// x"
    