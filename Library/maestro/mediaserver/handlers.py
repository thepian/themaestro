from thepian.conf import structure
from themaestro.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web

class CssHandler(tornado.web.RequestHandler):
    def get(self,file_name):
        self.write("You requested the main page")

        from os.path import join,isdir

        src = join(structure.CSS_DIR,file_name)
        if not isdir(src):
            raise Http404
        target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
        if newer_assets(src,target):
            lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
            with open(target,"w") as f:
                f.write(''.join(lines))

        # if nginx in front accelerate
        response = HttpResponse('',mimetype="text/css")
        response['X-Accel-Redirect'] = "/targetmedia/css/"+file_name
        return response


class JsHandler(tornado.web.RequestHandler):
    def get(self, file_name):
        from os.path import join,isdir
        from distutils.dep_util import newer_group

        src = join(structure.JS_DIR,file_name)
        if not isdir(src):
            raise Http404
        target = join(structure.MEDIASITE_DIRS[-1],"js",file_name)
        if newer_assets(src,target) or request.GET.get("force",False):
            lines = combine_asset_sources(src,structure.JS_DIR,source_node=JsSourceNode)
            with open(target,"w") as f:
                f.write(''.join(lines))

        # if nginx in front accelerate
        response = HttpResponse('',mimetype="text/javascript")
        response['X-Accel-Redirect'] = "/targetmedia/js/"+file_name
        return response

application = tornado.web.Application([
    (r"/css/(\w+\.css)", CssHandler),
    (r"/js/(\w+\.js)", JsHandler),
])

