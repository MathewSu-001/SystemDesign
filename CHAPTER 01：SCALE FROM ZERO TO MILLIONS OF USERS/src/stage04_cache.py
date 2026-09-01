"""Stage 04：保留 Stage 03 架構，加入 Shared Cache 與 Cache-Aside。"""

import queue
import socket
import threading
import time
from dataclasses import dataclass, field


DOMAIN = "www.mysite.com"
PUBLIC_IP = "15.125.23.214"
LOCAL_HOST = "127.0.0.1"
LOAD_BALANCER_PORT = 8080
REPLICATION_DELAY = 1.0
CACHE_TTL = 2.0
REQUEST_COUNT = 8


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
        print("[Replication] 已排入背景同步；Replicas 暫時可能仍是舊資料")
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
class CacheEntry:
    value: str
    expires_at: float


class SharedCache:
    """所有 Web Servers 共用、具有 TTL 的記憶體 Cache。"""

    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.data: dict[str, CacheEntry] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> str | None:
        with self.lock:
            entry = self.data.get(key)
            if entry is None:
                print(f"[Cache] MISS {key}")
                return None
            if time.monotonic() >= entry.expires_at:
                del self.data[key]
                print(f"[Cache] EXPIRED {key}")
                return None
            print(f"[Cache] HIT {key} -> {entry.value}")
            return entry.value

    def set(self, key: str, value: str) -> None:
        with self.lock:
            self.data[key] = CacheEntry(value, time.monotonic() + self.ttl)
        print(f"[Cache] SET {key}={value}; TTL={self.ttl:.1f}s")

    def delete(self, key: str) -> None:
        with self.lock:
            existed = self.data.pop(key, None) is not None
        print(f"[Cache] DELETE {key} ({'invalidated' if existed else 'already empty'})")


DATABASE = ReplicatedDatabase()
CACHE = SharedCache(CACHE_TTL)


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
    data_source: str,
    cache_status: str,
) -> bytes:
    body_bytes = body.encode("utf-8")
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"X-Served-By: {web_server}\r\n"
        f"X-Data-Source: {data_source}\r\n"
        f"X-Cache: {cache_status}\r\n"
        "Connection: close\r\n\r\n"
    )
    return headers.encode("utf-8") + body_bytes


def run_web_server(backend: Backend, ready: threading.Event, stop: threading.Event) -> None:
    """GET 使用 Cache-Aside；POST/PUT 先寫 Primary，再刪除 Cache。"""
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
                if path != "/profile":
                    response = build_response(
                        "404 Not Found", "not found", backend.name, "none", "BYPASS"
                    )
                elif method in ("POST", "PUT"):
                    node = DATABASE.write("profile", body)
                    CACHE.delete("profile")
                    response = build_response(
                        "200 OK", f"saved: {body}", backend.name, node.name, "INVALIDATED"
                    )
                elif method == "GET":
                    value = CACHE.get("profile")
                    if value is not None:
                        response = build_response(
                            "200 OK", value, backend.name, "Shared Cache", "HIT"
                        )
                    else:
                        value, node = DATABASE.read("profile")
                        if value is not None:
                            CACHE.set("profile", value)
                        response = build_response(
                            "200 OK" if value is not None else "404 Not Found",
                            value or "profile not found",
                            backend.name,
                            node.name,
                            "MISS",
                        )
                else:
                    response = build_response(
                        "405 Method Not Allowed", "method not allowed", backend.name, "none", "BYPASS"
                    )
                connection.sendall(response)


def proxy(request: bytes, backend: Backend) -> bytes:
    with socket.create_connection((LOCAL_HOST, backend.local_port), timeout=2) as upstream:
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
        print(f"[Load Balancer] {PUBLIC_IP}:80 -> {LOCAL_HOST}:{LOAD_BALANCER_PORT}")
        ready.set()
        for _ in range(REQUEST_COUNT):
            connection, _address = server.accept()
            with connection:
                request = connection.recv(4096)
                backend = BACKENDS[next_backend]
                next_backend = (next_backend + 1) % len(BACKENDS)
                print(f"[Load Balancer] Round Robin -> {backend.name}")
                connection.sendall(proxy(request, backend))


def run_browser(number: int, method: str, body: str = "") -> None:
    body_bytes = body.encode("utf-8")
    request = (
        f"{method} /profile HTTP/1.1\r\nHost: {DOMAIN}\r\n"
        f"Content-Length: {len(body_bytes)}\r\nConnection: close\r\n\r\n"
    ).encode("utf-8") + body_bytes
    with socket.create_connection((LOCAL_HOST, LOAD_BALANCER_PORT), timeout=2) as client:
        client.sendall(request)
        chunks = []
        while chunk := client.recv(4096):
            chunks.append(chunk)
    headers, response_body = b"".join(chunks).decode("utf-8").split("\r\n\r\n", 1)
    lines = headers.split("\r\n")
    values = {
        line.split(": ", 1)[0]: line.split(": ", 1)[1]
        for line in lines[1:]
        if ": " in line
    }
    print(
        f"[Browser] Request {number}: {method} <- {lines[0]}; "
        f"{values['X-Served-By']}; cache={values['X-Cache']}; "
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
        raise RuntimeError("Load Balancer 啟動逾時")

    print(f"[DNS] {DOMAIN} -> {PUBLIC_IP}\n")
    run_browser(1, "POST", "Alice v1")
    print("[Wait] 等待 Replicas 完成第一次同步...\n")
    time.sleep(1.2)
    run_browser(2, "GET")  # MISS：從 Replica 取得 v1 並寫入 Cache
    run_browser(3, "GET")  # HIT：另一台 Web Server 共用相同 Cache
    run_browser(4, "GET")  # HIT
    run_browser(5, "PUT", "Alice v2")  # 更新 Primary 並清除 Cache
    run_browser(6, "GET")  # MISS：Replica 落後，舊 v1 被放回 Cache
    print("[Wait] 等待 Replicas 追上 Primary，但 Cache 尚未過期...\n")
    time.sleep(1.2)
    run_browser(7, "GET")  # HIT：仍讀到 Cache 中的舊 v1
    print("[Wait] 等待 Cache TTL 到期...\n")
    time.sleep(1.0)
    run_browser(8, "GET")  # EXPIRED/MISS：Replica 已是 v2

    load_balancer_thread.join(3)
    DATABASE.events.put(None)
    replication_thread.join(3)
    stop.set()
    for thread in web_threads:
        thread.join(1)


if __name__ == "__main__":
    main()

