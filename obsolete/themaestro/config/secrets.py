from random import choice

def make_secrets():
    def mks():
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
        
    secrets_contents = ["%s: ('%s','%s','%s',),\n" % (i,mks(),mks(),mks()) for i in range(2 ** 16)]
    secrets_contents.insert(0,'VERIFICATION_SECRET = { # (device, user, session) verification secrets\n')
    secrets_contents.append('}\n')
    return secrets_contents

