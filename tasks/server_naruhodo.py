#!/usr/bin/env python
# -*- coding: utf-8 -*-

import SimpleHTTPServer
import SocketServer

class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        body = b'Naruhodo'
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-length', len(body))
        self.end_headers()
        self.wfile.write(body)
        try:
            csv_file = open("./datas/csv/naruhodo.csv", "a")
            csv_file.write("1\n")
            csv_file.close()
        except:
            pass

PORT = 8000

# Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
Handler = MyHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()