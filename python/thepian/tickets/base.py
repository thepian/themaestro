"""
base.py

Created by Henrik Vendelbo on 2008-05-01.
Copyright (c) 2008 Thepian. All rights reserved.
"""
from types import MethodType
import binascii,random, socket, hashlib
from math import sqrt
from time import time,sleep, gmtime
from datetime import datetime
import calendar
from thepian.conf import structure 
from thepian.exceptions import IdentitySuspicious
from thepian.utils import ip4_to_ip6

def common_get_secret(self):
    """Default get secret method"""
    return structure.AFFINITY_SECRET
    
def get_device_secret(self):
    """Use the device encoding secret from secrets.py"""
    return structure.secrets.VERIFICATION_SECRET[self.number][0]

def get_user_secret(self):
    """Use the user encoding secret from secrets.py"""
    return structure.secrets.VERIFICATION_SECRET[self.number][1]

def get_session_secret(self):
    """Use the session encoding secret from secrets.py"""
    return structure.secrets.VERIFICATION_SECRET[self.number][2]
    
class IdentityPath(object):
    """Specify any number of top,middle,ipnumber,sub to pinpoint an affinity bucket,
    affinity number, entity, or asset"""
    
    static_path = False
    
    def __init__(self,*path,**kwargs):
        """Pass the individual path elements as parameters or a named parameter path_string.
        top & middle are coerced to integers
        If top & middle are not integers IdentityPath will still function, but static_path will be True
        """
        if "path_string" in kwargs:
            assert len(path) is 0
            path = kwargs["path_string"].split("/")
            if len(path[0]) == 0:
                del path[0]
        else:
            path = list(path)
        if len(path) > 0:
            try: path[0] = int(path[0]) 
            except ValueError: self.static_path = True
        if len(path) > 1:
            try: path[1] = int(path[1]) 
            except ValueError: self.static_path = True
        self.path = path
        
    def __repr__(self):
        return u"/" + u"/".join([str(p) for p in self.path])

    def __unicode__(self):
        return u"/" + u"/".join([str(p) for p in self.path])

    def __str__(self):
        return "/" + "/".join([str(p) for p in self.path])
        
    def __iter__(self):
        for e in self.path:
            yield e
            
    def __getitem__(self,index):
        if isinstance(index,slice): #TODO can't this be removed, slices should just work... or return a path instead
            return self.path[index]
        return self.path[index]
        
    def __len__(self):
        return len(self.path)
        
    def __cmp__(self,other):
        if isinstance(other,basestring):
            return cmp(self.__str__(),other)
        return self.path == other
            


class Identity(object):
    """ Object to hold encoded and decoded forms of a User/Device Identity. It contains original remote addr, first time, affinity number 
    
    Space is reserved for IPv6 addresses. Initial implementation uses ip v4 information storing it as 2002::xxxx:xxxx/128
    ip - 32 - 2002 0000 0000 0000 0000 0000 xxxx xxxx
    first time - 16 - datetime.utcnow() as microseconds
    number - 4 - random affinity number
    check - 40 - sha1 checksum using first part and device secret for the number
    changed - the encoded identity was changed.
    new - the encoded
    
    Create it:
    * from a 52/92 char encoded string
    * from a parent identity and a 16 char encoded string
    * from a path tuple
    
    Generate it:
    * specifying ip4/ip6
    * specifying ip4/ip6 and number
    """
    
    #TODO lastnumbers tuple while time is the same
    lasttime = 0
    lastnumber = -1
    
    generated = False
    
    def __init__(self,path=None,encoded=None,parent=None,ip4=None,ip6=None,number=None,range_number=structure.AFFINITY_NUMBER_MAX,get_secret=common_get_secret):
        """Create an identity from a string encoded form, or a blank instance"""
        self.get_secret = MethodType(get_secret, self, Identity)

        if encoded:
            if parent and len(encoded) == 16:
                self.__set(encoded,parent=parent)
            else:
                self.__set(encoded)
        elif path:
            if len(path) == 4:
                top, middle, iptime, sub = path
                self.__set(sub,parent=Identity(encoded="%s%x" % (iptime,int(top) * structure.AFFINITY_NUMBER_SPLIT + int(middle))))
            else:
                top, middle, iptime = path
                self.__set("%s%4x" % (iptime,int(top) * structure.AFFINITY_NUMBER_SPLIT + int(middle)))
        else:
            """Generate first_time and number"""
            if parent:
                ip4 = parent.remote_addr
                number = parent.number
                self.parent = parent
            if ip6:
                self.remote_ip6 = ip6
                self.remote_addr = ip6
                #TODO remote_addr = ?
            if ip4:
                self.remote_addr = ip4
                self.remote_ip6 = ip4_to_ip6(ip4)
            number = number if number is not None else random.randint(0,structure.AFFINITY_NUMBER_MAX-1)
            now = datetime.utcnow()
            now = long(calendar.timegm(now.utctimetuple()) * 1000000) + now.microsecond
            while self.lasttime == now and number == self.lastnumber:
                sleep(.01)
                now = datetime.utcnow()
                now = long(calendar.timegm(now.utctimetuple()) * 1000000) + now.microsecond
            self.number = number
            Identity.lastnumber = number
            self.first_time = now
            Identity.lasttime = now
            self.encoded, check = self._encode_affinity()
            self.generated = True
            
            
    def __set(self,encoded,parent=None):
        """Set the encoded,parent attributes and extract derived attributes"""
        if parent:
            self.parent = parent
            self.encoded = parent.encoded[:32] + encoded + parent.encoded[48:52]
        else:
            self.encoded = encoded
        if len(self.encoded) in (52,92):
            self.remote_addr = self.extract_ip4()
            self.remote_ip6 = self.extract_ip6()
            self.first_time = self.extract_time()
            self.number = self.extract_number()
        #else:
        #    print len(self.encoded), "incorrect length for setting Identity", self.encoded


    def __get_without_checksum(self):
        return self.encoded[:52]
    without_checksum = property(__get_without_checksum)
    
    def __str__(self):
        return self.__get_without_checksum()
        
    def __repr__(self):
        try:
            check, check_result, check_pass = self.extract_check()
            return "%s (len=%s,%s)" % (self.__get_without_checksum(),len(self.encoded),
                len(self.encoded) == 52 and "unchecked" or check_pass and "pass" or "no pass")
        except AttributeError:
            #TODO figure out what derived class forgets to call init, and doesnt overide relevant methods
            return "identity unknown"
            
    def _encode_affinity(self):
        parts = []
        ip = socket.inet_aton(self.remote_addr)
        parts.append('200200000000000000000000')
        parts.append(binascii.hexlify(ip))

        parts.append("%016x" % self.first_time)

        parts.append("%04x" % self.number)

        # make a SHA checksum by combining with a secret key
        check = hashlib.sha1(''.join(parts + [self.get_secret(),])).hexdigest()
        parts.append(check)

        return ''.join(parts), check


    def extract_check(self):
        """Check the encoded against the hash
        If the identity is blank hashes will be blank
        If encoded doesn't contain a hash, encoded hash will be blank and match will be False
        returns: encoded hash, calculated hash on values, do they match?
        """
        if not self.encoded:
            return '','',True
        check_result = hashlib.sha1(self.encoded[:52] + self.get_secret()).hexdigest()
        if len(self.encoded) != 92:
            return '', check_result, False
        check = self.encoded[52:]
        return check, check_result, check == check_result 

    def extract_time(self):
      '''Extracts the time portion out of the guid and returns the 
         number of micro-seconds since the epoch'''
      return float(long(self.encoded[32:48], 16))

    def extract_number(self):
        '''Extracts the counter from the guid (returns the bits in decimal)'''
        return int(self.encoded[48:52], 16)

    def extract_ip4(self):
        '''Extracts the ip portion out of the guid and returns it
         as a string like 10.10.10.10'''
        # there's probably a more elegant way to do this
        thisip = []
        for index in range(24, 32, 2):
            thisip.append(str(int(self.encoded[index: index + 2], 16)))
        return '.'.join(thisip)
        
    def extract_ip6(self):
        '''Extracts the ip portion out of the guid and returns it
         as a string like 1000:1000...'''
        # there's probably a more elegant way to do this
        thisip = []
        for index in range(0, 32, 4):
            thisip.append(self.encoded[index: index + 4])
        return ':'.join(thisip)
        
    def get_first_datetime(self):
        return datetime.utcfromtimestamp(self.first_time / 1000000) 
    first_datetime = property(get_first_datetime)

    def get_path(self):
        """Return a tupple describing the path to the identity (top number,middle number,ip+stamp)"""
        top, middle = int(self.number / structure.AFFINITY_NUMBER_SPLIT), self.number % structure.AFFINITY_NUMBER_SPLIT
        if hasattr(self,'parent') and self.parent:
            return IdentityPath(top, middle, self.parent.encoded[:48],self.encoded[32:48])
            
        return IdentityPath(str(top),str(middle),self.encoded[:48])
    path = property(get_path)
    
    def get_subdomain(self):
        return structure.get_shard_subdomain(self.number)
    subdomain = property(get_subdomain)
    
    def get_url(self,base_domain,path=None):
        if not base_domain.startswith("."):
            base_domain = "."+base_domain
        return "http://%s%s%s" % (self.subdomain, base_domain, path or self.path)

  
class VerifiedIdentity(Identity):
    
    def __init__(self,**kwargs):
        super(VerifiedIdentity,self).__init__(**kwargs)
        
        # extract_check
        if not self.check_pass:
            #TODO log it instead to security monitor
            print 'Failed affinity: %s , wrong: %s, correct: %s' % (self.encoded[:-40], self.check, self.check_result)
            if hasattr(self,'remote_addr') and hasattr(self,'first_time') and hasattr(self,'number'):
                print 'Remote %s, Time %s, Affinity %s' % (self.remote_addr, self.first_time, self.number)
            self.encoded = None
        
    def __str__(self):
        return self.encoded
    

class Affinity(Identity):
    """ Object to hold encoded and decoded forms of a User Device Affinity. It contains original remote addr, first time, shard name, affinity number 
    
        added attributes:
        cookie_expiry
        cookie_domain
        domain
        subdomain
    """
    
    def __init__(self,request_meta,**kwargs):
        """

        """
        super(Affinity,self).__init__(**kwargs)
            
        self.cookie_expiry = structure.AFFINITY_EXPIRY
        self.cookie_domain = structure.machine.to_cookie_domain(request_meta.get('HTTP_HOST',structure.machine.DOMAINS[0]))
        self.base_domain = structure.get_base_domain(request_meta)
        
    def _get_domain(self):
        return self.subdomain + self.base_domain
    domain = property(_get_domain)
    
    def as_dl(self):
        check, check_result, check_pass = self.extract_check()
        entries = (
            ("Shard Domain",self.domain),
            ("Affinity Path",self.path),
            ("Affinity Number",self.number),
            ("First Access",self.first_datetime),
            ("First ip",self.extract_ip4()),
            ("Affinity Pass",check_pass and "True" or "False"),
            ("Affinity Check", check_result)
        )
        return u"".join([u"<dt>%s</dt><dd>%s</dd>" % (k,v) for k,v in entries])
    
    
class IdentityAccess(object):
    """Manage access permissions list

    Answers questions such as:    
    Does this identity have ____(level) access to ____(http/db) ____(domain) ___(path)
    
    One url can have more than one access level granted as a single page or tree.
    
    When encoded the questions and answers are packed as a string with ANSI separators.
    \x1E record separator
    \x1F unit separator
    With the structure:
    ( (question,until,proof), (question,until,proof) )
    
    flags:
    generated
    changed   
    """
    PAGE_QUESTION_TEMPLATE = "page %s access to %s://%s %s"
    TREE_QUESTION_TEMPLATE = "tree %s access to %s://%s %s"
    
    changed = False
    generated = False
    
    def __init__(self,request_meta,identity,encoded=None):
        self.identity = identity
        self.cookie_expiry = structure.AFFINITY_EXPIRY
        self.cookie_domain = structure.machine.to_cookie_domain(request_meta.get('HTTP_HOST',structure.machine.DOMAINS[0]))
        self.base_domain = structure.get_base_domain(request_meta)
        if encoded:
            self._decode(encoded)
            self.generated = False
        else:
            self._generate()
            self.generated = True
        import secrets
        self.secret = secrets.VERIFICATION_SECRET[self.identity.number][0]
            
    def _generate(self):
        self.permissions = {} # dict of tuples
            
    def _decode(self,encoded):
        self.permissions = {}
        for entry in encoded.split('\x1E'):
            try:
                se = entry.split('\x1F')
                if len(se) == 3:
                    self.permissions[se[0]] = se
            except:
                pass

    def _encode(self):
        r = []
        for question in self.permissions:
            r.append('\x1F'.join(self.permissions[question]))
        return '\x1E'.join(r)
        
    encoded = property(_encode)
    
    def as_dl(self):
        return u"".join([u"<dt>%s</dt><dd>%s until %s</dd>" % (q,p,long(u,16)) for q,u,p in self.permissions.itervalues()])
    
    def __getitem__(self,question):
        """Returns (question digest,use until,proof,expected proof)"""
        qd = hashlib.sha1(question).hexdigest()
        if qd not in self.permissions:
            return (qd,0,"",None)
        question_digest,use_until,proof = self.permissions[qd]
        p = hashlib.sha1()
        p.update(self.identity.without_checksum)
        p.update(question) #free text question
        p.update(use_until) #in seconds in hex as in cookie
        p.update(self.secret)
        pd = p.hexdigest()
        return (question_digest,long(use_until,16),proof,pd)
    
    def check_access(self,level,type,domain,path,now=None):
        #TODO option to check for tree access
        if not now:
            now = calendar.timegm(datetime.now().utctimetuple())
        q = self.PAGE_QUESTION_TEMPLATE % (level,type,domain,path)
        qd, use_until, proof, expected = self[q]
        if proof == expected and use_until > now:
            return True

        sp = path.split("/")
        if path != "/":
            for i in range(len(sp),1,-1):
                q = self.TREE_QUESTION_TEMPLATE % (level,type,domain,"/".join(sp[:i]))
                qd, use_until, proof, expected = self[q]
                if proof == expected and use_until > now:
                    return True
        q = self.TREE_QUESTION_TEMPLATE % (level,type,domain,"/")
        qd, use_until, proof, expected = self[q]
        return proof == expected and use_until > now
        
    def grant_access(self,level,type,domain,path,use_until,page=False):
        use_until_hex = "%08x" % calendar.timegm(use_until.utctimetuple())
        if page:
            q = self.PAGE_QUESTION_TEMPLATE % (level,type,domain,path)
        else:
            q = self.TREE_QUESTION_TEMPLATE % (level,type,domain,path)
        qd = hashlib.sha1(q).hexdigest()
        p = hashlib.sha1()
        p.update(self.identity.without_checksum)
        p.update(q)
        p.update(use_until_hex)
        p.update(self.secret)
        pd = p.hexdigest()
        if qd not in self.permissions or self.permissions[qd][1] != pd:
            self.changed = True
        self.permissions[qd] = (qd,use_until_hex,pd)

    def deny_access(self,level,type,domain,path,page=False):
        if page:
            q = self.PAGE_QUESTION_TEMPLATE % (level,type,domain,path)
        else:
            q = self.TREE_QUESTION_TEMPLATE % (level,type,domain,path)
        qd = hashlib.sha1(q).hexdigest()
        if qd in self.permissions:
            del self.permissions[qd]
            self.changed = True
