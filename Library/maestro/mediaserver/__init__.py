from thepian.conf import structure
import tornado.web

from handlers import HomeHandler, CssHandler, JsHandler

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/css/(\w+\.css)", CssHandler),
            (r"/js/(\w+\.js)", JsHandler),
        ]
        settings = dict(
            blog_title=u"Tornado Blog",
            template_path=structure.TEMPLATES_DIR,
            static_path=structure.MEDIASITE_DIRS[0],
            # ui_modules={"Entry": EntryModule},
            xsrf_cookies=True,
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            # login_url="/auth/login",
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # # Have one global connection to the blog DB across all handlers
        # self.db = tornado.database.Connection(
        #     host=options.mysql_host, database=options.mysql_database,
        #     user=options.mysql_user, password=options.mysql_password)
        # 
        #     application = tornado.web.Application([
        #     ])