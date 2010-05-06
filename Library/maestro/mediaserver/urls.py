from handlers import *

urls = [
    (r"/", HomeHandler),
    (r"/css/(\w+\.css)", CssHandler),
    (r"/js/(\w+\.js)/verify/(.*)", JsVerifyHandler),
    (r"/js/(\w+)/verify/(.*)", JsVerifyHandler),
    (r"/js/verify", JsVerifyAllHandler),
    (r"/js/(\w+\.js)", JsHandler),
    (r"/js/(\w+\.jo)", JoHandler),
]
