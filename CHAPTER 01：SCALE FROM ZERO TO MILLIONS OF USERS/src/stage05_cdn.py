"""Stage 05：保留 Stage 04 架構，在 Client 與 Origin 之間加入 CDN。"""

import queue
import socket
import threading
import time
from dataclasses import dataclass, field


DOMAIN = "www.mysite.com"
CDN_PUBLIC_IP = "203.0.113.10"
ORIGIN_PUBLIC_IP = "15.125.23.214"
LOCAL_HOST = "127.0.0.1"
CDN_PORT = 8070
LOAD_BALANCER_PORT = 8080
REPLICATION_DELAY = 1.0
APP_CACHE_TTL = 2.0
CDN_CACHE_TTL = 3.0
BROWSER_REQUEST_COUNT = 8
ORIGIN_REQUEST_COUNT = 5


@dataclass
class DatabaseNode:
    name: str
    private_ip: str
    data: dict[str, str] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def read(self, key: str) -> str | None:
        with self.lock:
            return self.data.get(key)

    def write(self, key: str, value: str) -> None:
        with self.lock:
            self.data[key] = value


class ReplicatedDatabase:
    """寫入 Primary、輪流讀取 Replicas，並在背景非同步複製。"""

    def __init__(self) -> None:
        self.primary = DatabaseNode("Database Primary", "10.0.2.10")
        self.replicas = [
            DatabaseNode("Database Replica 1", "10.0.2.11"),
            DatabaseNode("Database Replica 2", "10.0.2.12"),
        ]
        self.next_replica = 0
        self.events: queue.Queue[tuple[str, str] | None] = queue.Queue()

    def write(self, key: str, value: str) -> DatabaseNode:
        self.primary.write(key, value)
        print(f"[{self.primary.name}] WRITE {key}={value}")
        self.events.put((key, value))
        return self.primary

    def read(self, key: str) -> tuple[str | None, DatabaseNode]:
        replica = self.replicas[self.next_replica]
        self.next_replica = (self.next_replica + 1) % len(self.replicas)
        value = replica.read(key)
        print(f"[{replica.name}] READ {key} -> {value or '<not found>'}")
        return value, replica

    def replicate(self) -> None:
        while True:
            event = self.events.get()
            if event is None:
                self.events.task_done()
                return
            key, value = event
            time.sleep(REPLICATION_DELAY)
            for replica in self.replicas:
                replica.write(key, value)
                print(f"[Replication] Primary -> {replica.name}: {key}={value}")
            self.events.task_done()


@dataclass
class TimedEntry:
    value: str | bytes
    expires_at: float


class SharedApplicationCache:
    """Web Servers 共用的 Application Cache，保存 Database 查詢結果。"""

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.data: dict[str, TimedEntry] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> str | None:
        with self.lock:
            entry = self.data.get(key)
            if entry is None:
                print(f"[App Cache] MISS {key}")
                return None
            if time.monotonic() >= entry.expires_at:
                del self.data[key]
                print(f"[App Cache] EXPIRED {key}")
                return None
            print(f"[App Cache] HIT {key} -> {entry.value}")
            return str(entry.value)

    def set(self, key: str, value: str) -> None:
        with self.lock:
            self.data[key] = TimedEntry(value, time.monotonic() + self.ttl)
        print(f"[App Cache] SET {key}={value}; TTL={self.ttl:.1f}s")

    def delete(self, key: str) -> None:
        with self.lock:
            self.data.pop(key, None)
        print(f"[App Cache] DELETE {key}")


class CDNEdgeCache:
    """保存完整 Origin HTTP Response 的 CDN Edge Cache。"""

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.data: dict[str, TimedEntry] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> tuple[bytes | None, str]:
        with self.lock:
            entry = self.data.get(key)
            if entry is None:
                print(f"[CDN] MISS {key}")
                return None, "MISS"
            if time.monotonic() >= entry.expires_at:
                del self.data[key]
                print(f"[CDN] EXPIRED {key}")
                return None, "EXPIRED"
            print(f"[CDN] HIT {key}")
            return bytes(entry.value), "HIT"

    def set(self, key: str, response: bytes) -> None:
        with self.lock:
            self.data[key] = TimedEntry(response, time.monotonic() + self.ttl)
        print(f"[CDN] SET {key}; TTL={self.ttl:.1f}s")


class StaticOrigin:
    """模擬由 Origin Web Servers 提供的版本化前靜態內容。"""

    def __init__(self) -> None:
        self.data = {"/static/logo.txt": "System Design Logo v1"}
        self.lock = threading.Lock()

    def read(self, path: str) -> str | None:
        with self.lock:
            return self.data.get(path)

    def deploy(self, path: str, content: str) -> None:
        with self.lock:
            self.data[path] = content
        print(f"[Deployment] Origin 更新 {path} -> {content}")


DATABASE = ReplicatedDatabase()
APP_CACHE = SharedApplicationCache(APP_CACHE_TTL)
CDN_CACHE = CDNEdgeCache(CDN_CACHE_TTL)
STATIC_ORIGIN = StaticOrigin()


@dataclass
class Backend:
    name: str
    private_ip: str
    local_port: int


BACKENDS = [
    Backend("Web Server 1", "10.0.1.11", 9001),
    Backend("Web Server 2", "10.0.1.12", 9002),
    Backend("Web Server 3", "10.0.1.13", 9003),
]


def parse_request(request: bytes) -> tuple[str, str, str]:
    text = request.decode("utf-8")
    headers, _, body = text.partition("\r\n\r\n")
    try:
        method, path, _version = headers.split("\r\n", 1)[0].split(" ")
    except ValueError:
        return "", "/bad-request", ""
    return method, path, body


def build_response(
    status: str,
    body: str,
    web_server: str,
    app_cache: str = "BYPASS",
    data_source: str = "Origin",
) -> bytes:
    body_bytes = body.encode("utf-8")
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"X-Served-By: {web_server}\r\n"
        f"X-App-Cache: {app_cache}\r\n"
        f"X-Data-Source: {data_source}\r\n"
        "Connection: close\r\n\r\n"
    )
    return headers.encode("utf-8") + body_bytes


def add_cdn_header(response: bytes, status: str) -> bytes:
    """CDN 在送給 Browser 前加入這次 Edge Cache 的處理結果。"""
    headers, separator, body = response.partition(b"\r\n\r\n")
    if status == "HIT":
        lines = headers.split(b"\r\n")
        headers = b"\r\n".join(
            b"X-Data-Source: CDN Edge"
            if line.startswith(b"X-Data-Source:")
            else line
            for line in lines
        )
    return headers + f"\r\nX-CDN-Cache: {status}".encode() + separator + body


def run_web_server(backend: Backend, ready: threading.Event, stop: threading.Event) -> None:
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, backend.local_port))
        server.listen()
        server.settimeout(0.2)
        ready.set()
        while not stop.is_set():
            try:
                connection, _address = server.accept()
            except socket.timeout:
                continue
            with connection:
                method, path, body = parse_request(connection.recv(4096))
                print(f"[{backend.name}] {method} {path}")
                if method == "GET" and path.startswith("/static/"):
                    content = STATIC_ORIGIN.read(path)
                    response = build_response(
                        "200 OK" if content else "404 Not Found",
                        content or "not found",
                        backend.name,
                        data_source="Static Origin",
                    )
                elif path == "/profile" and method in ("POST", "PUT"):
                    node = DATABASE.write("profile", body)
                    APP_CACHE.delete("profile")
                    response = build_response(
                        "200 OK", f"saved: {body}", backend.name, "INVALIDATED", node.name
                    )
                elif path == "/profile" and method == "GET":
                    value = APP_CACHE.get("profile")
                    if value is not None:
                        response = build_response(
                            "200 OK", value, backend.name, "HIT", "Shared App Cache"
                        )
                    else:
                        value, node = DATABASE.read("profile")
                        if value is not None:
                            APP_CACHE.set("profile", value)
                        response = build_response(
                            "200 OK" if value else "404 Not Found",
                            value or "profile not found",
                            backend.name,
                            "MISS",
                            node.name,
                        )
                else:
                    response = build_response("404 Not Found", "not found", backend.name)
                connection.sendall(response)


def forward(request: bytes, port: int) -> bytes:
    with socket.create_connection((LOCAL_HOST, port), timeout=2) as upstream:
        upstream.sendall(request)
        chunks = []
        while chunk := upstream.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks)


def run_load_balancer(ready: threading.Event) -> None:
    next_backend = 0
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, LOAD_BALANCER_PORT))
        server.listen()
        print(f"[Origin Load Balancer] {ORIGIN_PUBLIC_IP}:80 -> {LOCAL_HOST}:{LOAD_BALANCER_PORT}")
        ready.set()
        for _ in range(ORIGIN_REQUEST_COUNT):
            connection, _address = server.accept()
            with connection:
                request = connection.recv(4096)
                backend = BACKENDS[next_backend]
                next_backend = (next_backend + 1) % len(BACKENDS)
                print(f"[Origin Load Balancer] Round Robin -> {backend.name}")
                connection.sendall(forward(request, backend.local_port))


def is_cdn_cacheable(method: str, path: str) -> bool:
    return method == "GET" and path.startswith("/static/")


def run_cdn_edge(ready: threading.Event) -> None:
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, CDN_PORT))
        server.listen()
        print(f"[CDN Edge] {CDN_PUBLIC_IP}:443 -> {LOCAL_HOST}:{CDN_PORT}")
        ready.set()
        for _ in range(BROWSER_REQUEST_COUNT):
            connection, _address = server.accept()
            with connection:
                request = connection.recv(4096)
                method, path, _body = parse_request(request)
                if not is_cdn_cacheable(method, path):
                    print(f"[CDN] BYPASS {method} {path}")
                    response = forward(request, LOAD_BALANCER_PORT)
                    connection.sendall(add_cdn_header(response, "BYPASS"))
                    continue

                cache_key = f"{DOMAIN}{path}"
                response, cache_status = CDN_CACHE.get(cache_key)
                if response is None:
                    response = forward(request, LOAD_BALANCER_PORT)
                    status_line = response.split(b"\r\n", 1)[0]
                    if b" 200 " in status_line:
                        CDN_CACHE.set(cache_key, response)
                connection.sendall(add_cdn_header(response, cache_status))


def run_browser(number: int, method: str, path: str, body: str = "") -> None:
    body_bytes = body.encode("utf-8")
    request = (
        f"{method} {path} HTTP/1.1\r\nHost: {DOMAIN}\r\n"
        f"Content-Length: {len(body_bytes)}\r\nConnection: close\r\n\r\n"
    ).encode() + body_bytes
    response = forward(request, CDN_PORT).decode("utf-8")
    headers, response_body = response.split("\r\n\r\n", 1)
    lines = headers.split("\r\n")
    values = {
        line.split(": ", 1)[0]: line.split(": ", 1)[1]
        for line in lines[1:]
        if ": " in line
    }
    print(
        f"[Browser] Request {number}: {method} {path} <- {lines[0]}; "
        f"cdn={values['X-CDN-Cache']}; app={values['X-App-Cache']}; "
        f"source={values['X-Data-Source']}; body={response_body!r}\n"
    )


def main() -> None:
    stop = threading.Event()
    web_threads = []
    for backend in BACKENDS:
        ready = threading.Event()
        thread = threading.Thread(target=run_web_server, args=(backend, ready, stop), daemon=True)
        thread.start()
        if not ready.wait(2):
            raise RuntimeError(f"{backend.name} 啟動逾時")
        web_threads.append(thread)

    replication_thread = threading.Thread(target=DATABASE.replicate, daemon=True)
    replication_thread.start()
    load_balancer_ready = threading.Event()
    load_balancer_thread = threading.Thread(
        target=run_load_balancer, args=(load_balancer_ready,), daemon=True
    )
    load_balancer_thread.start()
    if not load_balancer_ready.wait(2):
        raise RuntimeError("Origin Load Balancer 啟動逾時")

    cdn_ready = threading.Event()
    cdn_thread = threading.Thread(target=run_cdn_edge, args=(cdn_ready,), daemon=True)
    cdn_thread.start()
    if not cdn_ready.wait(2):
        raise RuntimeError("CDN Edge 啟動逾時")

    print(f"[DNS] {DOMAIN} -> CDN Edge {CDN_PUBLIC_IP}\n")
    run_browser(1, "POST", "/profile", "Alice v1")
    time.sleep(1.2)
    run_browser(2, "GET", "/static/logo.txt")  # CDN MISS，取得 Logo v1
    run_browser(3, "GET", "/static/logo.txt")  # CDN HIT
    run_browser(4, "GET", "/profile")  # CDN BYPASS，使用 App Cache/Database
    STATIC_ORIGIN.deploy("/static/logo.txt", "System Design Logo v2")
    run_browser(5, "GET", "/static/logo.txt")  # CDN HIT，仍為 Logo v1
    print("[Wait] 等待 CDN TTL 到期...\n")
    time.sleep(CDN_CACHE_TTL + 0.2)
    run_browser(6, "GET", "/static/logo.txt")  # EXPIRED，向 Origin 取得 Logo v2
    run_browser(7, "GET", "/static/logo.txt")  # CDN HIT Logo v2
    run_browser(8, "GET", "/profile")  # CDN BYPASS

    cdn_thread.join(3)
    load_balancer_thread.join(3)
    DATABASE.events.put(None)
    replication_thread.join(3)
    stop.set()
    for thread in web_threads:
        thread.join(1)


if __name__ == "__main__":
    main()
