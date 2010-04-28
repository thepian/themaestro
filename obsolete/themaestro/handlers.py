from themaestro.sources import CssSourceNode,JsSourceNode, newer_assets, combine_asset_sources

import tornado.web

class CssHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("You requested the main page")

class JsHandler(tornado.web.RequestHandler):
    def get(self, story_id):
        self.write("You requested the story " + story_id)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/story/([0-9]+)", StoryHandler),
])

def generate_css(request, file_name):
    from os.path import join,isdir

    src = join(structure.CSS_DIR,file_name)
    if not isdir(src):
        raise Http404
    target = join(structure.MEDIASITE_DIRS[-1],"css",file_name)
    if newer_assets(src,target):
        lines = combine_asset_sources(src,structure.CSS_DIR,source_node=CssSourceNode)
        with open(target,"w") as f:
            f.write(''.join(lines))
    
    response = HttpResponse('',mimetype="text/css")
    response['X-Accel-Redirect'] = "/targetmedia/css/"+file_name
    return response

