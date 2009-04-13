from datetime import datetime
from thepian.tickets.base import IdentityPath,Identity,Affinity,IdentityAccess

page_encoded = 'f71cd3af5e055dbe99dfb800ec1eeec101c5435a\x1f3afff4417f\x1f02b2f3fc1965c42ccd712e65708d527283bebc25'
tree_encoded = '1a51dec011b80fa44dde7c39fef6d537526f2755\x1f3afff4417f\x1fe699d1f70e006f1d7d2008c63ef8ffe312804212'

level = "extra"
type = "http"
domain = "www.idolyzed.local"
path = "/some/path"
path2 = "/some"
path3 = "/somewhere/else
request_meta = { 'HTTP_HOST':"www.idolyzed.local" }
identity = Identity(encoded='2002000000000000000000007f00000100045e41adf14c581662') #'2002000000000000000000007f00000100045e41adf14c581662b637d715a8e39efdcd37061bd243d4313eedf744'

"todo test: page vs tree, getitem, derived levels"

def test_init():
    access = IdentityAccess(request_meta,identity)
    assert access.generated
    assert not access.changed
    assert access.secret

def test_empty_getitem():
    access = IdentityAccess(request_meta,identity)
    qd, use_until, proof, expect = access[access.PAGE_QUESTION_TEMPLATE % (level,type,domain,path)]    
    assert qd == page_encoded[:40]
    assert use_until == 0
    qd, use_until, proof, expect = access[access.TREE_QUESTION_TEMPLATE % (level,type,domain,path)]    
    assert qd == tree_encoded[:40]
    assert use_until == 0
    
def test_page_getitem():
    access = IdentityAccess(request_meta,identity,encoded=page_encoded)
    qd, use_until, proof, expect = access[access.PAGE_QUESTION_TEMPLATE % (level,type,domain,path)]    
    assert qd == page_encoded[:40]
    assert use_until == 253402300799L
    assert proof == expect
    
def test_tree_getitem():
    access = IdentityAccess(request_meta,identity,encoded=tree_encoded)
    qd, use_until, proof, expect = access[access.TREE_QUESTION_TEMPLATE % (level,type,domain,path)]    
    assert qd == tree_encoded[:40]
    assert use_until == 253402300799L
    assert proof == expect
    
def test_page_grant():
    access = IdentityAccess(request_meta,identity)
    access.grant_access(level,type,domain,path,datetime.max,page=True)
    assert access.changed
    assert access.check_access(level,type,domain,path)
    
def test_tree_grant():
    access = IdentityAccess(request_meta,identity)
    access.grant_access(level,type,domain,path2,datetime.max,page=False)
    assert access.changed
    assert access.check_access(level,type,domain,path)
    assert access.check_access(level,type,domain,path2)
    assert not access.check_access(level,type,domain,"/")
    assert not access.check_access(level,type,domain,path3)
    
def test_deny():
    access = IdentityAccess(request_meta,identity)
    access.grant_access(level,type,domain,path,datetime.max,page=True)
    assert access.check_access(level,type,domain,path)
    access.deny_access(level,type,domain,path,page=True)    
    assert not access.check_access(level,type,domain,path)
    
def test_encoded():
    access = IdentityAccess(request_meta,identity,encoded=tree_encoded)
    assert access.permissions['f71cd3af5e055dbe99dfb800ec1eeec101c5435a']
    assert not access.generated
    assert not access.changed
    assert access.check_access(level,type,domain,path)
    assert access.check_access(level,type,domain,path2)
    assert not access.check_access(level,type,domain,"/")
    assert not access.check_access(level,type,domain,path3)
