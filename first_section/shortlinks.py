import json
import re
from typing import Dict, Any
from uuid import uuid4
import time


url_store = {}
rate_limit_store = {}

REQUEST_LIMIT = 10  
BLOCK_DURATION = 60 
RATE_LIMIT_RESET_INTERVAL = 60 

def generate_short_id():
    return str(uuid4())[:8]

class Server:
    async def __call__(self, scope: Dict[str, Any], receive, send) -> None:
        path = scope.get("path", "")
        method = scope.get("method", "").upper()
        client_ip = scope.get("client")[0]  

        if method == "GET" and path != "/":
            if not self.rate_limited(client_ip):
                await self.handle_get_redirect(path, send)
            else:
                await self.send_json(send, 429, {"error": "Too many requests, please try again later."})
        elif method == "POST" and path == "/shorten":
            await self.handle_post_shorten(receive, send, client_ip)
        else:
            await self.send_json(send, 404, {"error": "Route not found"})

    def rate_limited(self, client_ip: str) -> bool:
        current_time = time.time()
        request_data = rate_limit_store.get(client_ip, {"count": 0, "first_request_time": current_time})

        if current_time - request_data["first_request_time"] > RATE_LIMIT_RESET_INTERVAL:
            request_data = {"count": 0, "first_request_time": current_time}

        request_data["count"] += 1
        rate_limit_store[client_ip] = request_data

        if request_data["count"] > REQUEST_LIMIT:
            rate_limit_store[client_ip]["blocked_until"] = current_time + BLOCK_DURATION
            return True
        return False

    async def handle_get_redirect(self, path: str, send) -> None:
        short_id = path.lstrip("/")
        original_url = url_store.get(short_id)
        
        if original_url:
            await send({
                "type": "http.response.start",
                "status": 302,
                "headers": [(b"location", original_url.encode())],
            })
            await send({"type": "http.response.body", "body": b""})
        else:
            await self.send_json(send, 404, {"error": "URL not found"})

    async def handle_post_shorten(self, receive, send, client_ip: str) -> None:
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        try:
            data = json.loads(body.decode("utf-8"))
            original_url = data.get("original_url")
        except json.JSONDecodeError:
            await self.send_json(send, 400, {"error": "Invalid JSON format"})
            return

        if not original_url or not re.match(r'^https?://', original_url):
            await self.send_json(send, 400, {"error": "Invalid URL"})
            return

        short_id = generate_short_id()
        while short_id in url_store:
            short_id = generate_short_id()
        url_store[short_id] = original_url

        await self.send_json(send, 200, {"short_url": f"http://localhost:8000/{short_id}"})

    async def send_json(self, send: ASGISendCallable, status: int, data: Dict[str, Any]) -> None:
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps(data).encode(),
        })

app = Server()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
