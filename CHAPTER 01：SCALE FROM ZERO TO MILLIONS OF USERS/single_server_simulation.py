"""Chapter 01: DNS -> TCP -> HTTP -> HTML 的最小模擬。"""

import socket
import threading


DOMAIN = "www.mysite.com"
PUBLIC_IP = "15.125.23.214"

# PUBLIC_IP 是架構中的假設位址。本機沒有這個 IP，因此實際連線使用 localhost。
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8080


def resolve_domain(domain: str) -> str:
    """模擬 DNS：將指定網域解析成固定 IP。"""
    if domain != DOMAIN:
        raise LookupError(f"DNS 找不到網域：{domain}")

    print(f"[DNS] {domain} -> {PUBLIC_IP}")
    return PUBLIC_IP


def build_response(path: str) -> bytes:
    """根據請求路徑建立最小 HTTP Response。"""
    if path in ("/", "/index.html"):
        status = "200 OK"
        body = (
            "<!doctype html>"
            "<html><body><h1>Hello from the single server!</h1></body></html>"
        )
    else:
        status = "404 Not Found"
        body = "<!doctype html><html><body><h1>404 Not Found</h1></body></html>"

    body_bytes = body.encode("utf-8")
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return headers.encode("utf-8") + body_bytes


def run_web_server(ready: threading.Event) -> None:
    """啟動只處理一次請求的單一 Web Server。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((LOCAL_HOST, LOCAL_PORT))
        server.listen(1)

        print(f"[Server] 模擬公開位址：http://{PUBLIC_IP}")
        print(f"[Server] 本機監聽位址：http://{LOCAL_HOST}:{LOCAL_PORT}")
        ready.set()

        connection, client_address = server.accept()
        with connection:
            print(f"[TCP] 已接受 Client 連線：{client_address[0]}:{client_address[1]}")
            request = connection.recv(4096).decode("utf-8")
            request_line = request.split("\r\n", maxsplit=1)[0]
            print(f"[HTTP Request] {request_line}")

            try:
                method, path, _http_version = request_line.split(" ")
            except ValueError:
                method, path = "", "/bad-request"

            if method != "GET":
                path = "/bad-request"

            response = build_response(path)
            connection.sendall(response)
            print(f"[HTTP Response] {response.splitlines()[0].decode('utf-8')}")


def run_browser() -> None:
    """模擬 Browser：DNS 查詢、TCP 連線、發送 HTTP、接收 HTML。"""
    resolved_ip = resolve_domain(DOMAIN)
    print(f"[Browser] 準備連線到 {resolved_ip}:80")
    print(f"[Simulation] 將該連線映射到 {LOCAL_HOST}:{LOCAL_PORT}")

    request = (
        "GET /index.html HTTP/1.1\r\n"
        f"Host: {DOMAIN}\r\n"
        "Accept: text/html\r\n"
        "Connection: close\r\n"
        "\r\n"
    )

    with socket.create_connection((LOCAL_HOST, LOCAL_PORT), timeout=5) as client:
        print("[TCP] Browser 與 Web Server 的連線已建立")
        client.sendall(request.encode("utf-8"))

        chunks = []
        while chunk := client.recv(4096):
            chunks.append(chunk)

    response = b"".join(chunks).decode("utf-8")
    headers, html = response.split("\r\n\r\n", maxsplit=1)
    status_line = headers.split("\r\n", maxsplit=1)[0]

    print(f"[Browser] 收到：{status_line}")
    print(f"[Browser] HTML：{html}")


def main() -> None:
    server_ready = threading.Event()
    server_thread = threading.Thread(
        target=run_web_server,
        args=(server_ready,),
        daemon=True,
    )
    server_thread.start()

    server_ready.wait(timeout=5)
    if not server_ready.is_set():
        raise RuntimeError("Web Server 啟動逾時")

    run_browser()
    server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
