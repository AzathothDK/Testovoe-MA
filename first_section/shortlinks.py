from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4
import json
import re

url_store = {}


def generate_short_id():
    return str(uuid4())[:8]

class URLShorter(BaseHTTPRequestHandler):


    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"Сообщение": "URL укарачиватель запущен."}
            self.wfile.write(json.dumps(response).encode())
            return

        short_id = self.path.lstrip("/")
        original_url = url_store.get(short_id)

        if original_url:
            self.send_response(302)
            self.send_header("Location", original_url)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"Ошибка": "URL не найден"}
            try:
                self.wfile.write(json.dumps(response).encode())
            except BrokenPipeError:
                print("Клиент закрыл соединение до отправления ответа.")


    def do_POST(self):
        if self.path == "/shorten":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode("utf-8"))
            original_url = data.get("original_url")

            if not original_url or not re.match(r'^https?://', original_url):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"Ошибка": "неправльный URL"}
                self.wfile.write(json.dumps(response).encode())
                return

            short_id = generate_short_id()
            while short_id in url_store:
                short_id = generate_short_id()
            url_store[short_id] = original_url

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"short_url": f"http://localhost:8000/{short_id}"}
            self.wfile.write(json.dumps(response).encode())


def run(server_class=HTTPServer, handler_class=URLShorter, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Запускаю сервер на порту {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
