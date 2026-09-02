# CDN

## 一句話解釋

CDN 是將可快取的 HTTP 內容保存於靠近 Client 的 Edge Servers，讓 Cache Hit 不必回到 Origin 的分散式內容傳遞系統。

## 核心概念

- Browser 透過 DNS 或 CDN 的網路路由機制連線到適合且可用的 Edge Location，不一定只按照地理直線距離選擇。
- Edge Server 位於 CDN 網路邊緣，主要負責代理、快取與傳遞 HTTP Content。
- Origin 是 CDN 在 Cache Miss 或 Bypass 時轉送 Request 的上游 HTTP 服務，不等於 Database。
- Origin 可以是 Load Balancer、Web Server、Object Storage 或 API Gateway。
- CDN Cache 通常保存完整 HTTP Response，包含 Status、Headers 與 Body。
- CDN Hit 可以直接由 Edge 回傳；Miss 或 Expired 時需要向 Origin 取得內容。
- Bypass 表示 CDN 不使用這次 Request 的 Cache，直接將 Request 轉送 Origin。
- CDN 適合快取可公開共用且能接受短暫舊版本的內容，例如圖片、CSS 與 JavaScript。
- Shared Application Cache 位於 Web Server 與 Database 之間，和位於 Browser 與 Origin 之間的 CDN 解決不同問題。

## 程式對應位置

- [`CDNEdgeCache`](../src/stage05_cdn.py)：以 Thread-safe dictionary 模擬 CDN Edge Cache。
- [`run_cdn_edge()`](../src/stage05_cdn.py)：接收 Browser Request，決定 Hit、Miss、Expired 或 Bypass。
- [`is_cdn_cacheable()`](../src/stage05_cdn.py)：以 Method 與 Path 判斷是否使用 CDN Cache。
- [`add_cdn_header()`](../src/stage05_cdn.py)：加入 `X-CDN-Cache` 並標示 CDN Hit 的資料來源。
- [`CDN_PORT`](../src/stage05_cdn.py)：使用 `127.0.0.1:8070` 模擬 CDN Edge。
- [`LOAD_BALANCER_PORT`](../src/stage05_cdn.py)：使用 `127.0.0.1:8080` 模擬 CDN 後方的 Origin Endpoint。

