import time
import socket
import fcntl
import struct
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2

PORT = 8080
# def get_ip_address(ifname):
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     return socket.inet_ntoa(fcntl.ioctl(
#         s.fileno(),
#         -1071617759,  # SIOCGIFADDR
#         struct.pack('256s', ifname[:15].encode())
#     )[20:24])

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<h1>[DepthAI] Hello, world!</h1><p>Click <a href="img">here</a> for an image</p>')
        elif self.path == '/img':
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<h1>Video Feed!</h1><p>Video Stream Here</p>')
            except Exception as ex:
                print(str(ex))

with ThreadingSimpleServer(("", PORT), HTTPHandler) as httpd:
    print(f"Serving...")
    httpd.serve_forever()