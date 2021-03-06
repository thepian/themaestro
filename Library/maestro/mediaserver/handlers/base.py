import tornado.web

class ObjectLike(object):

    def __init__(self,d):
        self.data = d

    def __getitem__(self,key):
        if key not in self.data:
            return None
        return self.data[key]

    def __getattr__(self,key):
        if key not in self.data:
            return None
        return self.data[key]
        

class SpecRequestHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, core_api=None, run_script=None, upload_script_name=None):
        super(SpecRequestHandler,self).__init__(application, request)
        self.core_api = core_api
        self.run_script = run_script
        self.upload_script_name = upload_script_name

def getNodeId(request,account,project):
	# node cookie
	node_id = request.get_cookie("%s__%s__node" % (account,project),default=None)
	if node_id == None:
		import random, string
		node_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(20))
		print "new node id", node_id
		request.set_cookie("%s__%s__node" % (account,project), node_id, expires_days=365)
		
	return node_id
	
