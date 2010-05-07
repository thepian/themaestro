from handlers import *

urls = [
    (r"/", HomeHandler),
    (r"/css/(\w+\.css)", CssHandler),
    (r"/js/(\w+\.js)/verify/(.*)", JsVerifyHandler),
    (r"/js/(\w+)/(\w+\.js)/verify/(.*)", JsVerifyDetailHandler),
    (r"/js/verify", JsVerifyAllHandler),
    (r"/js/(\w+\.js)", JsHandler),
    (r"/js/(\w+\.jo)", JoHandler),
]
