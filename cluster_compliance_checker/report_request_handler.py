import http.server
from urllib.parse import urlparse


class ReportRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        bootstrap = "node_modules/bootstrap/dist"
        bootstrap_icons = "node_modules/bootstrap-icons"
        fonts = f"{bootstrap_icons}/font/fonts"
        paths_map = {
            "/": "report/report.html",
            "/logs": "report/logs.html",
            "/favicon.ico": "statics/favicon.ico",
            "/main.css": "statics/css/main.css",
            "/bootstrap.bundle.min.js": f"{bootstrap}/js/bootstrap.bundle.min.js",
            "/bootstrap.bundle.min.js.map": f"{bootstrap}/js/bootstrap.bundle.min.js.map",
            "/bootstrap.min.css": f"{bootstrap}/css/bootstrap.min.css",
            "/bootstrap.min.css.map": f"{bootstrap}/css/bootstrap.min.css.map",
            "/bootstrap-icons.css": f"{bootstrap_icons}/font/bootstrap-icons.css",
            "/fonts/bootstrap-icons.woff2": f"{fonts}/bootstrap-icons.woff2",
            "/fonts/bootstrap-icons.woff": f"{fonts}/bootstrap-icons.woff",
        }

        new_path = paths_map.get(urlparse(self.path).path)
        self.path = new_path or self.path

        return http.server.SimpleHTTPRequestHandler.do_GET(self)
