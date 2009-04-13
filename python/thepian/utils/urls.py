import re

PATH_RE = re.compile(r"^(\^)?(/)?([^/\$\(]*)(/)?([^\$]*)(\$)?$")

def regex2robots(reg):
    """
    Translates a urlpattern to a path segment(no leading /) for robots.txt
    ^stuff$ -> stuff
    With a few twists
    """
    basic = PATH_RE.match(reg)
    if not basic:
        raise Error, "URL pattern is not a basic regex '%s'" % reg
    groups = basic.groups()
    if groups[0] == "^" and groups[5] == "$" and groups[2] == "":
        return ""
    if groups[5] == "$" and not groups[3]:
        return groups[2]
    return groups[2] +"/"

