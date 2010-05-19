from thepian.conf import structure
import tornado.web, tornado.httpserver
from urls import urls

import socket
import os.path, os
try:
    import fcntl
except ImportError:
    if os.name == 'nt':
        import win32_support as fcntl
    else:
        raise



class HTTPServer(tornado.httpserver.HTTPServer):

    def bind(self, port, address=""):
        """Binds this server to the given port on the given IP address.

        To start the server, call start(). If you want to run this server
        in a single process, you can call listen() as a shortcut to the
        sequence of bind() and start() calls.
        """
        assert not self._socket
        if port:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            flags = fcntl.fcntl(self._socket.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self._socket.fileno(), fcntl.F_SETFD, flags)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setblocking(0)
            self._socket.bind((address, port))
            self._socket.listen(128)
        else:
            if os.path.exists(address): os.remove(address)
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
            self._socket.setblocking(0)
            self._socket.bind(address)
            self._socket.listen(128)
            


class Application(tornado.web.Application):
    def __init__(self,ioloop=None):
        self.ioloop = ioloop
        p = __path__[0]
        template_path = structure.TEMPLATES_DIR # (p+'/templates',structure.TEMPLATES_DIR)
        # print 'templates from: ',template_path
        settings = dict(
            # blog_title=u"Tornado Blog",
            debug=True,
            template_path=template_path,
            static_path=structure.MEDIASITE_DIRS[0],
            # ui_modules={"Entry": EntryModule},
            xsrf_cookies=True,
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            # login_url="/auth/login",
        )
        tornado.web.Application.__init__(self, urls, **settings)

        # # Have one global connection to the blog DB across all handlers
        # self.db = tornado.database.Connection(
        #     host=options.mysql_host, database=options.mysql_database,
        #     user=options.mysql_user, password=options.mysql_password)
        # 
        #     application = tornado.web.Application([
        #     ])
