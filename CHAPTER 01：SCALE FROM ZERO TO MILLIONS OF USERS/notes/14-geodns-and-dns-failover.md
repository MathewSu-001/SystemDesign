# GeoDNS 與 DNS Failover

## 一句話解釋

GeoDNS 是 Authoritative DNS 依 Client 或 Resolver 的區域、服務健康狀態與路由政策回傳不同 DNS Answer，讓新的連線前往適合的 Data Center。

## 核心概念

- GeoDNS 仍然使用 DNS Protocol，不是取代 DNS 的另一套協定。
- 一般 DNS Record 可能對所有查詢者回傳相同 IP；GeoDNS 可以對不同區域回傳不同 Data Center IP。
- GeoDNS 處理 DNS Query，不會接收 Browser 後續的 HTTP Request。
- Browser 取得 IP 後，會直接建立 TCP／TLS Connection 至選定的 Data Center Endpoint。
- GeoDNS 通常看到 DNS Resolver 的來源位置，不一定是終端 Client 的精確位置。
- Data Center 不健康時，GeoDNS 可以停止在新的 DNS Answer 中回傳該 Data Center。
- Browser、Operating System 與 DNS Resolver 都可能依 TTL 快取 DNS Answer。
- 已快取舊 IP 的 Client 在 TTL 到期前可能繼續連向故障 Data Center，因此 DNS-based Failover 不保證立即完成。
- 降低 TTL 可以縮短部分 Cache 保存舊答案的時間，但會增加 DNS Query 數量，也不能完全控制所有中間 Cache 與既有連線。

## DNS 與 HTTP 是兩個階段

DNS 階段：

```text
Browser -> DNS Resolver -> GeoDNS
Browser <- Taipei Data Center IP
```

HTTP 階段：

```text
Browser -> Taipei Data Center Load Balancer -> Web Server
```

GeoDNS 不在第二段 HTTP Data Path 中。相較之下，Load Balancer／Reverse Proxy 會接收並轉送實際 HTTP Request。

## GeoDNS Routing

正常情況：

```text
Asia Query -> Taipei healthy  -> Taipei IP; route=LOCAL
US Query   -> Virginia healthy -> Virginia IP; route=LOCAL
```

Taipei 故障後的新查詢：

```text
Asia Query -> Taipei unhealthy -> Virginia IP; route=FAILOVER
```

實際產品除了區域與健康狀態，也可能考慮 Latency、Capacity、Traffic Weight、法規或維護狀態。

## DNS Cache 與 Failover 時間

```text
T0：Browser 查到 Taipei IP，TTL=60 秒
T10：Taipei Data Center 故障
T20：Browser 仍使用 Cache 中的 Taipei IP
T60：TTL 到期，Browser 重新查詢
T60：GeoDNS 回傳 Virginia IP
```

GeoDNS 能改變之後的 DNS Answer，但無法主動修改所有 Browser 與 Resolver 已保存的舊答案。

## GeoDNS、Global Reverse Proxy 與 Anycast

| 技術 | 決策時機 | 是否處理 HTTP Request | 常見選擇範圍 |
| --- | --- | --- | --- |
| GeoDNS | DNS Query | 否 | Region／Data Center |
| Global Reverse Proxy | Connection／HTTP Request | 是 | Region、Service 或 Backend |
| Anycast | Internet Routing | Anycast 本身不解析 HTTP | 鄰近或可達的 Edge Endpoint |

它們不是必然互斥，正式系統可能組合使用。例如 GeoDNS 先選 Global Endpoint，Anycast 將封包送往適合的 Edge，再由 Reverse Proxy 選擇後方服務。

## 程式對應位置

- [`GeoDNS`](../src/stage07_multi_data_center.py)：依 Client Region 與 Data Center 健康狀態選擇 DNS Answer。
- [`GeoDNS.resolve()`](../src/stage07_multi_data_center.py)：回傳 Data Center、路由狀態與 TTL，不代理 HTTP Request。
- [`DNSCacheEntry`](../src/stage07_multi_data_center.py)：保存 Browser 已取得的 Data Center 與到期時間。
- [`Browser.resolve()`](../src/stage07_multi_data_center.py)：模擬 Browser DNS Cache 的 Hit、Set 與重新查詢。
- [`GEO_DNS_TTL`](../src/stage07_multi_data_center.py)：設定兩秒教學用 DNS TTL。
- [`main()`](../src/stage07_multi_data_center.py)：展示故障後舊 DNS Answer 造成的 `503`，以及 TTL 到期後的 Failover。

