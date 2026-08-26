# DNS

## 一句話解釋

DNS 是讓 Client 查詢網域名稱相關紀錄的分散式命名系統，常見用途是取得服務的 IP 位址。

## 核心概念

- 網域名稱必須先經過 DNS 解析，Client 才知道要連線到哪個 IP。
- A Record 將名稱對應至 IPv4 位址；AAAA Record 則對應 IPv6 位址。
- CNAME Record 將一個名稱設定為另一個名稱的別名。
- DNS Resolver 代表 Client 進行查詢，Authoritative DNS 提供特定 Zone 的最終答案。
- TTL 決定 DNS 回應可以被快取多久。
- 網域與 IP 不一定一對一，可以多個網域共用一個 IP，也可以一個網域對應多個 IP。
- 本章使用固定對應 `www.mysite.com → 15.125.23.214`，沒有發送真正的 DNS Query。

## 程式對應位置

- [`DOMAIN` 與 `PUBLIC_IP`](../src/stage01_single_server.py)：定義模擬的網域與公開 IP。
- [`resolve_domain()`](../src/stage01_single_server.py)：檢查網域並回傳固定 IP，模擬 DNS Lookup。
- [`run_browser()`](../src/stage01_single_server.py)：在建立 TCP 連線前呼叫 DNS 模擬。
