from handlers import *

urls = [
    (r"/", HomeHandler),
    (r"/css/(\w+\.css)", CssHandler),
    (r"/js/(\w+\.js)/(.*)", JsTestHandler),
    (r"/js/(\w+\.js)", JsHandler),
    (r"/js/(\w+\.jo)", JoHandler),
]
