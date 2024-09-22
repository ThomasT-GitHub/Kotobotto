# Description: This file is used to keep the bot alive on Azure. It starts a simple HTTP server that listens on port 8080.
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Health check received")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")


def run_server():
    print("Starting HTTP server for health checks...")
    server_address = ("", 8080)  # Listen on all available interfaces, port 8080
    httpd = HTTPServer(server_address, KeepAliveHandler)
    httpd.serve_forever()


def keep_alive():
    t = Thread(target=run_server)
    t.start()
