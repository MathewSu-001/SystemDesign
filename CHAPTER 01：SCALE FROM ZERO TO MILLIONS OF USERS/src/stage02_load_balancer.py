"""Stage 02：以 Round Robin 模擬 Load Balancer 與多台 Web Server。

架構中的公開與私有 IP 無法直接綁定在一般本機環境，因此程式使用
127.0.0.1 的不同 Port 模擬每個元件，並在輸出中保留架構位址。
"""

import socket
import threading
from dataclasses import dataclass


DOMAIN = "www.mysite.com"
LOAD_BALANCER_PUBLIC_IP = "15.125.23.214"
LOCAL_HOST = "127.0.0.1"
LOAD_BALANCER_PORT = 8080
REQUEST_COUNT = 6


@dataclass
class Backend:
    """Load Balancer Server Pool 中的一台 Web Server。"""

    name: str
    private_ip: str
    local_port: int
    online: threading.Event


BACKENDS = [
    Backend("Web Server 1", "10.0.1.11", 9001, threading.Event()),
    Backend("Web Server 2", "10.0.1.12", 9002, threading.Event()),
    Backend("Web Server 3", "10.0.1.13", 9003, threading.Event()),
]


def resolve_domain(domain: str) -> str:
    """模擬 DNS：網域只解析到 Load Balancer 的公開 IP。"""
    if domain != DOMAIN:
        raise LookupError(f"DNS 找不到網域：{domain}")

    print(f"[DNS] {domain} -> {LOAD_BALANCER_PUBLIC_IP}")
    return LOAD_BALANCER_PUBLIC_IP


def parse_path(request: bytes) -> str:
    """從最小 HTTP Request 中取出 Path。"""
    request_line = request.decode("utf-8").split("\r\n", maxsplit=1)[0]
    try:
        _method, path, _version = request_line.split(" ")
    except ValueError:
        return "/bad-request"
    return path


def build_response(status: str, body: str, server_name: str) -> bytes:
    """建立包含處理節點名稱的最小 HTTP Response。"""
    body_bytes = body.encode("utf-8")
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"X-Served-By: {server_name}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers.encode("utf-8") + body_bytes


def run_web_server(
    backend: Backend,
    ready: threading.Event,
    stop: threading.Event,
) -> None:
    """持續接受 Health Check 與應用程式 Request。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, backend.local_port))
        server.listen()
        server.settimeout(0.2)
        ready.set()

        while not stop.is_set():
            try:
                connection, _client_address = server.accept()
            except socket.timeout:
                continue

            with connection:
                request = connection.recv(4096)
                path = parse_path(request)

                if path == "/health":
                    status = "200 OK" if backend.online.is_set() else "503 Unavailable"
                    response = build_response(status, "", backend.name)
                elif not backend.online.is_set():
                    response = build_response(
                        "503 Service Unavailable",
                        "<h1>Server unavailable</h1>",
                        backend.name,
                    )
                elif path in ("/", "/index.html"):
                    print(f"[{backend.name}] 處理 {path}")
                    response = build_response(
                        "200 OK",
                        f"<h1>Hello from {backend.name}!</h1>",
                        backend.name,
                    )
                else:
                    response = build_response(
                        "404 Not Found",
                        "<h1>404 Not Found</h1>",
                        backend.name,
                    )

                connection.sendall(response)


def is_healthy(backend: Backend) -> bool:
    """透過 HTTP /health 檢查後端是否能接收 Request。"""
    health_request = (
        "GET /health HTTP/1.1\r\n"
        f"Host: {backend.private_ip}\r\n"
        "Connection: close\r\n\r\n"
    ).encode("utf-8")

    try:
        with socket.create_connection(
            (LOCAL_HOST, backend.local_port), timeout=1
        ) as connection:
            connection.sendall(health_request)
            status_line = connection.recv(4096).split(b"\r\n", maxsplit=1)[0]
            return b" 200 " in status_line
    except OSError:
        return False


class RoundRobinLoadBalancer:
    """只在健康 Backend 之間輪流選擇的 Load Balancer。"""

    def __init__(self, backends: list[Backend]) -> None:
        self.backends = backends
        self.next_backend_index = 0

    def choose_backend(self) -> Backend | None:
        """從上次停止處往後找第一台健康的 Backend。"""
        healthy_names = {
            backend.name for backend in self.backends if is_healthy(backend)
        }
        health_summary = ", ".join(
            f"{backend.name}={'healthy' if backend.name in healthy_names else 'unhealthy'}"
            for backend in self.backends
        )
        print(f"[Health Check] {health_summary}")

        for offset in range(len(self.backends)):
            index = (self.next_backend_index + offset) % len(self.backends)
            backend = self.backends[index]
            if backend.name in healthy_names:
                self.next_backend_index = (index + 1) % len(self.backends)
                return backend
        return None


def proxy_request(request: bytes, backend: Backend) -> bytes:
    """建立第二條 TCP 連線，將 Request 轉送至選中的 Backend。"""
    with socket.create_connection(
        (LOCAL_HOST, backend.local_port), timeout=2
    ) as upstream:
        upstream.sendall(request)
        chunks = []
        while chunk := upstream.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks)


def run_load_balancer(ready: threading.Event) -> None:
    """接受 Browser 連線，選擇 Backend 並代理 HTTP 訊息。"""
    load_balancer = RoundRobinLoadBalancer(BACKENDS)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, LOAD_BALANCER_PORT))
        server.listen()
        print(f"[Load Balancer] 公開位址：http://{LOAD_BALANCER_PUBLIC_IP}:80")
        print(
            "[Simulation] Load Balancer 映射至 "
            f"http://{LOCAL_HOST}:{LOAD_BALANCER_PORT}"
        )
        ready.set()

        for _ in range(REQUEST_COUNT):
            connection, _client_address = server.accept()
            with connection:
                request = connection.recv(4096)
                backend = load_balancer.choose_backend()

                if backend is None:
                    response = build_response(
                        "503 Service Unavailable",
                        "<h1>No healthy backend</h1>",
                        "Load Balancer",
                    )
                else:
                    print(
                        "[Load Balancer] Round Robin -> "
                        f"{backend.name} ({backend.private_ip})"
                    )
                    try:
                        response = proxy_request(request, backend)
                    except OSError:
                        response = build_response(
                            "502 Bad Gateway",
                            "<h1>Backend connection failed</h1>",
                            "Load Balancer",
                        )

                connection.sendall(response)


def run_browser(request_number: int) -> None:
    """向 Load Balancer 發送一次 HTTP Request 並顯示處理節點。"""
    request = (
        "GET /index.html HTTP/1.1\r\n"
        f"Host: {DOMAIN}\r\n"
        "Accept: text/html\r\n"
        "Connection: close\r\n\r\n"
    ).encode("utf-8")

    with socket.create_connection(
        (LOCAL_HOST, LOAD_BALANCER_PORT), timeout=2
    ) as client:
        client.sendall(request)
        chunks = []
        while chunk := client.recv(4096):
            chunks.append(chunk)

    response = b"".join(chunks).decode("utf-8")
    headers, _body = response.split("\r\n\r\n", maxsplit=1)
    header_lines = headers.split("\r\n")
    served_by = next(
        line.split(": ", maxsplit=1)[1]
        for line in header_lines
        if line.startswith("X-Served-By:")
    )
    print(f"[Browser] Request {request_number} <- {served_by}\n")


def main() -> None:
    """啟動三台 Web Server、Load Balancer 與 Browser 模擬。"""
    stop = threading.Event()
    backend_ready_events = []
    backend_threads = []

    for backend in BACKENDS:
        backend.online.set()
        ready = threading.Event()
        thread = threading.Thread(
            target=run_web_server,
            args=(backend, ready, stop),
            daemon=True,
        )
        thread.start()
        backend_ready_events.append(ready)
        backend_threads.append(thread)

    for ready in backend_ready_events:
        if not ready.wait(timeout=2):
            raise RuntimeError("Web Server 啟動逾時")

    load_balancer_ready = threading.Event()
    load_balancer_thread = threading.Thread(
        target=run_load_balancer,
        args=(load_balancer_ready,),
        daemon=True,
    )
    load_balancer_thread.start()
    if not load_balancer_ready.wait(timeout=2):
        raise RuntimeError("Load Balancer 啟動逾時")

    resolved_ip = resolve_domain(DOMAIN)
    print(f"[Browser] 所有 Request 都送往 {resolved_ip}:80\n")

    for request_number in range(1, REQUEST_COUNT + 1):
        if request_number == 4:
            BACKENDS[1].online.clear()
            print("[Failure] Web Server 2 已離線\n")
        run_browser(request_number)

    load_balancer_thread.join(timeout=3)
    stop.set()
    for thread in backend_threads:
        thread.join(timeout=1)


if __name__ == "__main__":
    main()
