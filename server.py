import os
import http.server
import socketserver
import urllib

from http import HTTPStatus


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        msg = 'Hello At-Eases!!! you requested %s' % (self.path)
        self.wfile.write(msg.encode())

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(post_data.encode(encoding='utf_8'))


port = int(os.getenv('PORT', 80))
print('Listening on port %s' % (port))
httpd = socketserver.TCPServer(('', port), Handler)
httpd.serve_forever()
