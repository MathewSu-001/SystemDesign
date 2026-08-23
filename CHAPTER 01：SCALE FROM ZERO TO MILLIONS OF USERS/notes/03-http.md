# HTTP

## 一句話解釋

HTTP 是 Client 以 Request 請求資源、Server 以 Response 回傳結果的應用層協定。

## 核心概念

- HTTP 訊息透過 TCP 連線傳送，本章使用 HTTP/1.1。
- Request 包含 Request Line、Headers，以及可選的 Body。
- Response 包含 Status Line、Headers，以及可選的 Body。
- `GET /index.html HTTP/1.1` 表示使用 HTTP/1.1 讀取 `/index.html`。
- `Host` Header 指出 Client 要存取的網域。
- Headers 與 Body 之間以空行 `\r\n\r\n` 分隔。
- `Content-Type` 描述 Body 格式，`Content-Length` 表示 Body 的 Byte 長度。
- 本章成功時回傳 `200 OK` 和 HTML，路徑不存在時回傳 `404 Not Found`。

## 程式對應位置

- [`run_browser()`](../src/single_server_simulation.py)：組合並發送 HTTP Request，再解析 HTTP Response。
- [`run_web_server()`](../src/single_server_simulation.py)：接收並解析 Request Line，取得 Method 與 Path。
- [`build_response()`](../src/single_server_simulation.py)：根據 Path 建立 Status Line、Headers 與 HTML Body。
- [`sendall()` 與 `recv()`](../src/single_server_simulation.py)：透過 TCP 傳送與接收 HTTP 訊息。
