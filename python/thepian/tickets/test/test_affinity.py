from datetime import datetime
from thepian.tickets.base import IdentityPath,Identity,Affinity

def test_entity_path():
    p1 = IdentityPath('111','165','2002000000000000000000007f00000100045793a668e30a')
    p2 = IdentityPath(path_string="/111/165/2002000000000000000000007f00000100045793a668e30a")
    assert len(p1) == 3
    assert len(p2) == 3
    assert str(p1) == "/111/165/2002000000000000000000007f00000100045793a668e30a"
    def listing(*l):
        assert len(l) == 3
        assert l[0] == 111
        assert l[1] == 165
    listing(*p1) # testing __iter__
    assert p1[0] == 111
    assert p1 == "/111/165/2002000000000000000000007f00000100045793a668e30a"
    
def test_asset_path():
    p3 = IdentityPath('111','165','2002000000000000000000007f00000100045793a668e30a','00045793a668e30a')
    assert len(p3) == 4
    assert str(p3) == repr(p3)
    assert unicode(p3) == u"/111/165/2002000000000000000000007f00000100045793a668e30a/00045793a668e30a"
    assert p3 == u"/111/165/2002000000000000000000007f00000100045793a668e30a/00045793a668e30a"
    
def test_identity():
    id1 = Identity(ip4='127.0.0.5')
    check, check_result, check_pass = id1.extract_check()
    assert id1.remote_addr == '127.0.0.5'
    assert check_pass
    assert id1.first_datetime <= datetime.utcnow()
    id2 = Identity(encoded=id1.encoded)
    assert id1.remote_ip6 == id2.remote_ip6
    #assert id1.first_datetime == id2.first_datetime, "%s .. %s" % (str(id1.first_datetime),str(id2.first_datetime))
    assert id1.number == id2.number
    
    
def test_uniqueness():
    known = set()
    for i in range(1,100):
        id1 = Identity(ip4='127.0.0.5')
        assert id1.encoded not in known
        known.add(id1.encoded)
        id2 = Identity(ip4='127.0.0.%s' % i)
        assert id2.encoded not in known
        known.add(id2.encoded)
        id3 = Identity(ip4='127.0.0.111',number=55)
        assert id3.encoded not in known
        known.add(id3.encoded)
        
def test_encoded_unchecked():
    # 52 chars no check
    id1 = Identity(encoded="2002000000000000000000007f00000100045793a668e3014eb1")
    check, check_result, check_pass = id1.extract_check()
    assert not check_pass
    assert check == ""
    assert check_result == "b14dda66fd1a1a50df9b23ffc92c503a315829fd"
    assert id1.without_checksum == "2002000000000000000000007f00000100045793a668e3014eb1"
    assert str(id1) == "2002000000000000000000007f00000100045793a668e3014eb1"
    assert unicode(id1) == u"2002000000000000000000007f00000100045793a668e3014eb1"
    assert id1.encoded == "2002000000000000000000007f00000100045793a668e3014eb1"

    id2 = Identity(path=('111','165','2002000000000000000000007f00000100045793a668e301'))
    assert id2.encoded == "2002000000000000000000007f00000100045793a668e3014eb1"
    assert id2.remote_addr == "127.0.0.1"
    
def test_encoded_checked():
    # 92 chars with check
    id2 = Identity(encoded="2002000000000000000000007f00000100045793a668e3014eb1b14dda66fd1a1a50df9b23ffc92c503a315829fd")
    check, check_result, check_pass = id2.extract_check()
    assert check == "b14dda66fd1a1a50df9b23ffc92c503a315829fd"
    assert check_result == "b14dda66fd1a1a50df9b23ffc92c503a315829fd", "len=%s, new hash=%s" % (len(id2.encoded),check_result)
    assert check_pass
    
    id3 = Identity(encoded="2002000000000000000000007f00000100045793a668e3014eb1ab3b6adedc87c403809ceb05f5897017f0147645")
    check, check_result, check_pass = id3.extract_check()
    assert not check_pass
    assert check == "ab3b6adedc87c403809ceb05f5897017f0147645"
    assert check_result == "b14dda66fd1a1a50df9b23ffc92c503a315829fd"
    
def test_with_parent():
    id3 = Identity(encoded="2002000000000000000000007f00000100045793a668e3014eb1ab3b6adedc87c403809ceb05f5897017f0147645")
    id4 = Identity(parent=id3,encoded="00045793a668e30a")
    assert id4.encoded == "2002000000000000000000007f00000100045793a668e30a4eb1"
    assert id4.parent == id3
    assert id4.path[2] == id3.without_checksum[:-4]
    assert id4.path == ('111','165',id3.without_checksum[:-4],"00045793a668e30a"), str(id4.path)
    assert id4.path == "/%s/%s/%s/%s" % ('111','165',id3.without_checksum[:-4],"00045793a668e30a")
    
    id5 = Identity(parent=id3)
    assert id5.parent == id3
    assert id5.path[2] == id3.without_checksum[:-4]
    
