"""Stage 03：保留 Load Balancer 與多台 Web Server，加入資料庫讀寫分離。"""

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
REQUEST_COUNT = 6


@dataclass
class DatabaseNode:
    """使用記憶體 dictionary 模擬一個資料庫節點。"""

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
    """寫入 Primary、輪流讀取 Replicas，並在背景進行非同步複製。"""

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
        print("[Replication] 已排入背景同步；Replica 暫時可能仍是舊資料")
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


DATABASE = ReplicatedDatabase()


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


def resolve_domain(domain: str) -> str:
    if domain != DOMAIN:
        raise LookupError(f"DNS 找不到網域：{domain}")
    print(f"[DNS] {domain} -> {PUBLIC_IP}")
    return PUBLIC_IP


def parse_request(request: bytes) -> tuple[str, str, str]:
    text = request.decode("utf-8")
    headers, _, body = text.partition("\r\n\r\n")
    try:
        method, path, _version = headers.split("\r\n", 1)[0].split(" ")
    except ValueError:
        return "", "/bad-request", ""
    return method, path, body


def build_response(status: str, body: str, web: str, database: str) -> bytes:
    body_bytes = body.encode("utf-8")
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"X-Served-By: {web}\r\n"
        f"X-Database-Node: {database}\r\n"
        "Connection: close\r\n\r\n"
    )
    return headers.encode("utf-8") + body_bytes


def run_web_server(backend: Backend, ready: threading.Event, stop: threading.Event) -> None:
    """依 HTTP method 決定讀 Replica 或寫 Primary。"""
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
                    response = build_response("404 Not Found", "not found", backend.name, "none")
                elif method in ("POST", "PUT"):
                    node = DATABASE.write("profile", body)
                    response = build_response("200 OK", f"saved: {body}", backend.name, node.name)
                elif method == "GET":
                    value, node = DATABASE.read("profile")
                    status = "200 OK" if value is not None else "404 Not Found"
                    response = build_response(
                        status, value or "profile not found", backend.name, node.name
                    )
                else:
                    response = build_response(
                        "405 Method Not Allowed", "method not allowed", backend.name, "none"
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
    web = next(line.split(": ", 1)[1] for line in lines if line.startswith("X-Served-By:"))
    database = next(
        line.split(": ", 1)[1] for line in lines if line.startswith("X-Database-Node:")
    )
    print(
        f"[Browser] Request {number}: {method} <- {lines[0]}; "
        f"{web}; {database}; body={response_body!r}\n"
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

    print(f"[Browser] 所有 Request 都送往 {resolve_domain(DOMAIN)}:80\n")
    run_browser(1, "POST", "Alice v1")
    run_browser(2, "GET")  # Replica 尚未同步：找不到資料
    print("[Wait] 等待 1.2 秒讓 Replicas 追上...\n")
    time.sleep(1.2)
    run_browser(3, "GET")  # 已同步：Alice v1
    run_browser(4, "PUT", "Alice v2")
    run_browser(5, "GET")  # Replica 尚未同步：仍為 Alice v1
    print("[Wait] 等待 1.2 秒讓 Replicas 追上...\n")
    time.sleep(1.2)
    run_browser(6, "GET")  # 已同步：Alice v2

    load_balancer_thread.join(3)
    DATABASE.events.put(None)
    replication_thread.join(3)
    stop.set()
    for thread in web_threads:
        thread.join(1)


if __name__ == "__main__":
    main()
