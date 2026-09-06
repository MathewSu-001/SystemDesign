"""Stage 07：在 Stage 06 架構上加入 GeoDNS 與多資料中心 Failover。"""

import queue
import secrets
import socket
import threading
import time
from dataclasses import dataclass, field


DOMAIN = "www.mysite.com"
STATIC_DOMAIN = "static.mysite.com"
CDN_PUBLIC_IP = "203.0.113.10"
LOCAL_HOST = "127.0.0.1"
CDN_PORT = 8070
GEO_DNS_TTL = 2.0
REPLICATION_DELAY = 1.0
APP_CACHE_TTL = 2.0
CDN_CACHE_TTL = 3.0
SESSION_TTL = 30.0


@dataclass
class DatabaseNode:
    name: str
    data: dict[str, str] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def read(self, key: str) -> str | None:
        with self.lock:
            return self.data.get(key)

    def write(self, key: str, value: str) -> None:
        with self.lock:
            self.data[key] = value


class ReplicatedDatabase:
    """暫時由兩個 Data Centers 共用的 Primary 與 Replicas。"""

    def __init__(self) -> None:
        self.primary = DatabaseNode("Global Database Primary")
        self.replicas = [
            DatabaseNode("Global Database Replica 1"),
            DatabaseNode("Global Database Replica 2"),
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
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.data: dict[str, TimedEntry] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> str | None:
        with self.lock:
            entry = self.data.get(key)
            if entry is None:
                print(f"[Global App Cache] MISS {key}")
                return None
            if time.monotonic() >= entry.expires_at:
                del self.data[key]
                print(f"[Global App Cache] EXPIRED {key}")
                return None
            print(f"[Global App Cache] HIT {key} -> {entry.value}")
            return str(entry.value)

    def set(self, key: str, value: str) -> None:
        with self.lock:
            self.data[key] = TimedEntry(value, time.monotonic() + self.ttl)
        print(f"[Global App Cache] SET {key}={value}; TTL={self.ttl:.1f}s")

    def delete(self, key: str) -> None:
        with self.lock:
            self.data.pop(key, None)
        print(f"[Global App Cache] DELETE {key}")


@dataclass
class Session:
    user_id: str
    expires_at: float


class SharedSessionStore:
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self.data: dict[str, Session] = {}
        self.lock = threading.Lock()

    def create(self, user_id: str) -> str:
        session_id = secrets.token_urlsafe(24)
        with self.lock:
            self.data[session_id] = Session(user_id, time.monotonic() + self.ttl)
        print(f"[Global Session Store] SET {session_id} -> user_id={user_id}")
        return session_id

    def get(self, session_id: str) -> str | None:
        with self.lock:
            session = self.data.get(session_id)
            if session is None:
                print(f"[Global Session Store] MISS {session_id or '<missing>'}")
                return None
            if time.monotonic() >= session.expires_at:
                del self.data[session_id]
                print(f"[Global Session Store] EXPIRED {session_id}")
                return None
            print(f"[Global Session Store] HIT {session_id} -> user_id={session.user_id}")
            return session.user_id


class CDNEdgeCache:
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
    def __init__(self) -> None:
        self.data = {"/static/logo.txt": "System Design Logo v1"}

    def read(self, path: str) -> str | None:
        return self.data.get(path)


@dataclass
class Backend:
    name: str
    private_ip: str
    local_port: int


@dataclass
class DataCenter:
    name: str
    region: str
    public_ip: str
    load_balancer_port: int
    backends: list[Backend]
    healthy: bool = True


DATA_CENTERS = [
    DataCenter(
        "Taipei Data Center",
        "asia",
        "198.51.100.10",
        8081,
        [
            Backend("Taipei Web Server 1", "10.1.1.11", 9101),
            Backend("Taipei Web Server 2", "10.1.1.12", 9102),
        ],
    ),
    DataCenter(
        "Virginia Data Center",
        "us",
        "198.51.100.20",
        8082,
        [
            Backend("Virginia Web Server 1", "10.2.1.11", 9201),
            Backend("Virginia Web Server 2", "10.2.1.12", 9202),
        ],
    ),
]


class GeoDNS:
    """回傳 Data Center 位址；不代理後續 HTTP Request。"""

    def __init__(self, data_centers: list[DataCenter], ttl: float) -> None:
        self.data_centers = data_centers
        self.ttl = ttl

    def resolve(self, domain: str, client_region: str) -> tuple[DataCenter, str, float]:
        preferred = next(
            (dc for dc in self.data_centers if dc.region == client_region), None
        )
        if preferred and preferred.healthy:
            selected, route = preferred, "LOCAL"
        else:
            selected = next((dc for dc in self.data_centers if dc.healthy), None)
            if selected is None:
                raise RuntimeError("GeoDNS 找不到健康的 Data Center")
            route = "FAILOVER"
        print(
            f"[GeoDNS] {domain}; client={client_region} -> "
            f"{selected.name} {selected.public_ip}; route={route}; TTL={self.ttl:.1f}s"
        )
        return selected, route, self.ttl


DATABASE = ReplicatedDatabase()
APP_CACHE = SharedApplicationCache(APP_CACHE_TTL)
SESSION_STORE = SharedSessionStore(SESSION_TTL)
CDN_CACHE = CDNEdgeCache(CDN_CACHE_TTL)
STATIC_ORIGIN = StaticOrigin()
GEO_DNS = GeoDNS(DATA_CENTERS, GEO_DNS_TTL)


def parse_request(request: bytes) -> tuple[str, str, dict[str, str], str]:
    text = request.decode("utf-8")
    header_text, _, body = text.partition("\r\n\r\n")
    lines = header_text.split("\r\n")
    try:
        method, path, _version = lines[0].split(" ")
    except ValueError:
        return "", "/bad-request", {}, ""
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ": " in line:
            name, value = line.split(": ", 1)
            headers[name.lower()] = value
    return method, path, headers, body


def get_session_id(headers: dict[str, str]) -> str | None:
    for item in headers.get("cookie", "").split(";"):
        name, separator, value = item.strip().partition("=")
        if separator and name == "session_id":
            return value
    return None


def build_response(
    status: str,
    body: str,
    backend: str,
    data_center: str,
    app_cache: str = "BYPASS",
    session_store: str = "BYPASS",
    data_source: str = "Origin",
    extra_headers: dict[str, str] | None = None,
) -> bytes:
    body_bytes = body.encode("utf-8")
    headers = [
        f"HTTP/1.1 {status}",
        "Content-Type: text/plain; charset=utf-8",
        f"Content-Length: {len(body_bytes)}",
        f"X-Data-Center: {data_center}",
        f"X-Served-By: {backend}",
        f"X-App-Cache: {app_cache}",
        f"X-Session-Store: {session_store}",
        f"X-Data-Source: {data_source}",
        "Connection: close",
    ]
    if extra_headers:
        headers.extend(f"{name}: {value}" for name, value in extra_headers.items())
    return ("\r\n".join(headers) + "\r\n\r\n").encode() + body_bytes


def add_header(response: bytes, name: str, value: str) -> bytes:
    headers, separator, body = response.partition(b"\r\n\r\n")
    return headers + f"\r\n{name}: {value}".encode() + separator + body


def replace_header(response: bytes, name: str, value: str) -> bytes:
    headers, separator, body = response.partition(b"\r\n\r\n")
    prefix = f"{name}:".encode()
    lines = [
        f"{name}: {value}".encode() if line.startswith(prefix) else line
        for line in headers.split(b"\r\n")
    ]
    return b"\r\n".join(lines) + separator + body


def run_web_server(
    data_center: DataCenter,
    backend: Backend,
    ready: threading.Event,
    stop: threading.Event,
) -> None:
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
                method, path, headers, body = parse_request(connection.recv(4096))
                print(f"[{data_center.name}] [{backend.name}] {method} {path}")
                common = (backend.name, data_center.name)
                if method == "GET" and path.startswith("/static/"):
                    content = STATIC_ORIGIN.read(path)
                    response = build_response(
                        "200 OK" if content else "404 Not Found",
                        content or "not found",
                        *common,
                        data_source="Static Origin",
                    )
                elif method == "POST" and path == "/login":
                    user_id = body.strip()
                    if not user_id:
                        response = build_response(
                            "400 Bad Request", "user_id is required", *common
                        )
                    else:
                        session_id = SESSION_STORE.create(user_id)
                        response = build_response(
                            "200 OK",
                            f"logged in: {user_id}",
                            *common,
                            session_store="WRITE",
                            data_source="Global Session Store",
                            extra_headers={
                                "Set-Cookie": (
                                    f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax"
                                )
                            },
                        )
                elif method == "GET" and path == "/me":
                    user_id = SESSION_STORE.get(get_session_id(headers) or "")
                    response = build_response(
                        "200 OK" if user_id else "401 Unauthorized",
                        f"current user: {user_id}" if user_id else "login required",
                        *common,
                        session_store="HIT" if user_id else "MISS",
                        data_source="Global Session Store",
                    )
                elif path == "/profile" and method in ("POST", "PUT"):
                    node = DATABASE.write("profile", body)
                    APP_CACHE.delete("profile")
                    response = build_response(
                        "200 OK",
                        f"saved: {body}",
                        *common,
                        app_cache="INVALIDATED",
                        data_source=node.name,
                    )
                elif path == "/profile" and method == "GET":
                    value = APP_CACHE.get("profile")
                    if value is not None:
                        response = build_response(
                            "200 OK",
                            value,
                            *common,
                            app_cache="HIT",
                            data_source="Global App Cache",
                        )
                    else:
                        value, node = DATABASE.read("profile")
                        if value is not None:
                            APP_CACHE.set("profile", value)
                        response = build_response(
                            "200 OK" if value else "404 Not Found",
                            value or "profile not found",
                            *common,
                            app_cache="MISS",
                            data_source=node.name,
                        )
                else:
                    response = build_response("404 Not Found", "not found", *common)
                connection.sendall(response)


def forward(request: bytes, port: int) -> bytes:
    with socket.create_connection((LOCAL_HOST, port), timeout=2) as upstream:
        upstream.sendall(request)
        chunks = []
        while chunk := upstream.recv(4096):
            chunks.append(chunk)
    return b"".join(chunks)


def run_data_center_load_balancer(
    data_center: DataCenter,
    ready: threading.Event,
    stop: threading.Event,
) -> None:
    next_backend = 0
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, data_center.load_balancer_port))
        server.listen()
        server.settimeout(0.2)
        print(
            f"[{data_center.name} Load Balancer] {data_center.public_ip}:443 "
            f"-> {LOCAL_HOST}:{data_center.load_balancer_port}"
        )
        ready.set()
        while not stop.is_set():
            try:
                connection, _address = server.accept()
            except socket.timeout:
                continue
            with connection:
                request = connection.recv(4096)
                if not data_center.healthy:
                    print(f"[{data_center.name}] UNAVAILABLE")
                    connection.sendall(
                        build_response(
                            "503 Service Unavailable",
                            f"{data_center.name} is unavailable",
                            "No Backend",
                            data_center.name,
                            data_source="Data Center Failure",
                        )
                    )
                    continue
                backend = data_center.backends[next_backend]
                next_backend = (next_backend + 1) % len(data_center.backends)
                print(f"[{data_center.name} Load Balancer] Round Robin -> {backend.name}")
                connection.sendall(forward(request, backend.local_port))


def run_cdn_edge(ready: threading.Event, stop: threading.Event) -> None:
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, CDN_PORT))
        server.listen()
        server.settimeout(0.2)
        print(f"[CDN Edge] {CDN_PUBLIC_IP}:443 -> {LOCAL_HOST}:{CDN_PORT}")
        ready.set()
        while not stop.is_set():
            try:
                connection, _address = server.accept()
            except socket.timeout:
                continue
            with connection:
                request = connection.recv(4096)
                method, path, headers, _body = parse_request(request)
                cache_key = f"{STATIC_DOMAIN}{path}"
                response, cache_status = CDN_CACHE.get(cache_key)
                if response is None:
                    region = headers.get("x-client-region", "asia")
                    data_center, route, _ttl = GEO_DNS.resolve(DOMAIN, region)
                    response = forward(request, data_center.load_balancer_port)
                    response = add_header(response, "X-Traffic-Route", route)
                    if method == "GET" and b" 200 " in response.split(b"\r\n", 1)[0]:
                        CDN_CACHE.set(cache_key, response)
                elif cache_status == "HIT":
                    response = replace_header(response, "X-Data-Source", "CDN Edge")
                    response = replace_header(response, "X-Data-Center", "CDN Cache")
                    response = replace_header(response, "X-Traffic-Route", "CDN")
                connection.sendall(add_header(response, "X-CDN-Cache", cache_status))


@dataclass
class DNSCacheEntry:
    data_center: DataCenter
    route: str
    expires_at: float


class Browser:
    """模擬 Cookie 與 DNS TTL Cache；HTTP Request 不會經過 GeoDNS。"""

    def __init__(self, name: str, region: str) -> None:
        self.name = name
        self.region = region
        self.cookies: dict[str, str] = {}
        self.dns_cache: dict[str, DNSCacheEntry] = {}

    def resolve(self, domain: str) -> DNSCacheEntry:
        cached = self.dns_cache.get(domain)
        if cached and time.monotonic() < cached.expires_at:
            print(
                f"[{self.name} DNS Cache] HIT {domain} -> "
                f"{cached.data_center.public_ip}; route={cached.route}"
            )
            return cached
        data_center, route, ttl = GEO_DNS.resolve(domain, self.region)
        entry = DNSCacheEntry(data_center, route, time.monotonic() + ttl)
        self.dns_cache[domain] = entry
        print(f"[{self.name} DNS Cache] SET {domain}; TTL={ttl:.1f}s")
        return entry

    def request(self, number: int, method: str, path: str, body: str = "") -> None:
        body_bytes = body.encode()
        cookie = "; ".join(f"{key}={value}" for key, value in self.cookies.items())
        cookie_header = f"Cookie: {cookie}\r\n" if cookie else ""
        host = STATIC_DOMAIN if path.startswith("/static/") else DOMAIN
        request = (
            f"{method} {path} HTTP/1.1\r\nHost: {host}\r\n"
            f"X-Client-Region: {self.region}\r\n{cookie_header}"
            f"Content-Length: {len(body_bytes)}\r\nConnection: close\r\n\r\n"
        ).encode() + body_bytes

        if path.startswith("/static/"):
            print(f"[{self.name} DNS] {STATIC_DOMAIN} -> CDN Edge {CDN_PUBLIC_IP}")
            response = forward(request, CDN_PORT)
        else:
            destination = self.resolve(DOMAIN)
            response = forward(request, destination.data_center.load_balancer_port)
            response = add_header(response, "X-Traffic-Route", destination.route)

        header_text, response_body = response.decode().split("\r\n\r\n", 1)
        lines = header_text.split("\r\n")
        values = {
            line.split(": ", 1)[0]: line.split(": ", 1)[1]
            for line in lines[1:]
            if ": " in line
        }
        if "Set-Cookie" in values:
            name, value = values["Set-Cookie"].split(";", 1)[0].split("=", 1)
            self.cookies[name] = value
            print(f"[{self.name}] SAVE COOKIE {name}={value}")
        print(
            f"[{self.name}] Request {number}: {method} {path} <- {lines[0]}; "
            f"dc={values['X-Data-Center']}; route={values['X-Traffic-Route']}; "
            f"server={values['X-Served-By']}; session={values['X-Session-Store']}; "
            f"cdn={values.get('X-CDN-Cache', 'BYPASS')}; body={response_body!r}\n"
        )


def main() -> None:
    stop = threading.Event()
    threads: list[threading.Thread] = []

    for data_center in DATA_CENTERS:
        for backend in data_center.backends:
            ready = threading.Event()
            thread = threading.Thread(
                target=run_web_server,
                args=(data_center, backend, ready, stop),
                daemon=True,
            )
            thread.start()
            if not ready.wait(2):
                raise RuntimeError(f"{backend.name} 啟動逾時")
            threads.append(thread)

        ready = threading.Event()
        thread = threading.Thread(
            target=run_data_center_load_balancer,
            args=(data_center, ready, stop),
            daemon=True,
        )
        thread.start()
        if not ready.wait(2):
            raise RuntimeError(f"{data_center.name} Load Balancer 啟動逾時")
        threads.append(thread)

    replication_thread = threading.Thread(target=DATABASE.replicate, daemon=True)
    replication_thread.start()
    cdn_ready = threading.Event()
    cdn_thread = threading.Thread(
        target=run_cdn_edge, args=(cdn_ready, stop), daemon=True
    )
    cdn_thread.start()
    if not cdn_ready.wait(2):
        raise RuntimeError("CDN Edge 啟動逾時")
    threads.append(cdn_thread)

    asia_browser = Browser("Asia Browser", "asia")
    us_browser = Browser("US Browser", "us")

    asia_browser.request(1, "POST", "/login", "asia-user")
    asia_browser.request(2, "GET", "/me")
    us_browser.request(3, "POST", "/login", "us-user")
    us_browser.request(4, "GET", "/me")
    asia_browser.request(5, "GET", "/static/logo.txt")
    asia_browser.request(6, "GET", "/static/logo.txt")

    DATA_CENTERS[0].healthy = False
    print(f"[Failure] {DATA_CENTERS[0].name} DOWN\n")
    asia_browser.request(7, "GET", "/me")

    print("[Wait] 等待 Browser DNS Cache TTL 到期...\n")
    time.sleep(GEO_DNS_TTL + 0.2)
    asia_browser.request(8, "GET", "/me")

    stop.set()
    for thread in threads:
        thread.join(1)
    DATABASE.events.put(None)
    replication_thread.join(1)


if __name__ == "__main__":
    main()

