import socket
import pathlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime
import mimetypes
import json
import logging

BASE_DIR = pathlib.Path()
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
BUFER = 1024

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()


class MyHTTPHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        send_data_to_socket(body)        
        self.send_response(302)
        self.send_header('location', '/message')
        self.end_headers()
  


    def do_GET(self):

        roude = urllib.parse.urlparse(self.path)
        match roude.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                file = BASE_DIR / roude.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html")


    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')   
        self.end_headers()
        with open(filename, "br") as f:
            self.wfile.write(f.read())


    def send_static(self, filename):
        
        self.send_response(200)
        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type) 
        else:
            self.send_header('Content-Type', 'text/plain')  
        self.end_headers()
        with open(filename, "br") as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=MyHTTPHandler):

    adress = ("", 3000)
    http_server = server(adress, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    with open(BASE_DIR.joinpath("storage\data.json"), "r") as file:
        unpacked_content = json.load(file)
    try:
        payload = {key: value for key, value in [element.split("=") for element in body.split("&")]}
        date = datetime.now()
        content = {str(date): payload}
        unpacked_content.update(content)
        with open(BASE_DIR.joinpath("storage\data.json"), "w", encoding="utf-8") as file:
            json.dump(unpacked_content,file, ensure_ascii=False)
    except ValueError as err:
        logging.error(f"Feiled parse data {body} with error: {err}")
    except OSError as err:
        logging.error(f"Feiled write data {body} with error: {err}")



def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind((server))
    try:
        while True:
            data, adress = server_socket.recvfrom(BUFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info("Socket server stoped")
    finally:
        server_socket.close()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(threadName)s $(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()
     