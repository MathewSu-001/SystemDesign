# 007：加入多資料中心與 GeoDNS

## 狀態

已採用。

## 問題

Stage 06 只有一個 Origin Data Center。即使 Data Center 內有多台 Web Servers，整個 Data Center 因電力、網路或區域性事故失效時，服務仍無法使用；距離該 Data Center 很遠的 Client 也可能承受較高的網路延遲。

## 改動

- 保留 CDN、Stateless Web Tier、Shared Session Store、Shared Application Cache 與 Database Replication。
- 建立 Taipei 與 Virginia 兩個 Data Centers。
- 每個 Data Center 擁有自己的 Load Balancer 與兩台 Web Servers。
- 新增 GeoDNS，依 Client Region 回傳偏好的健康 Data Center IP。
- Browser 保存 DNS Answer，並在 TTL 到期前直接使用相同 Data Center 位址。
- 偏好的 Data Center 不健康時，新的 DNS Query 會回傳另一個健康 Data Center。
- 靜態內容改由 `static.mysite.com` 進入 CDN；動態內容由 `www.mysite.com` 的 GeoDNS Answer 導向 Data Center。

## Request 流程

動態 Request：

```text
Asia Browser -> GeoDNS Query: www.mysite.com
             <- Taipei Data Center IP + TTL

Asia Browser -> Taipei Load Balancer
             -> Taipei Web Server 1 or 2
             -> Shared Session Store / Cache / Database
```

靜態 Request：

```text
Browser -> static.mysite.com -> CDN Edge
                              ├-> HIT -> Browser
                              └-> MISS -> Healthy Origin Data Center
```

GeoDNS 只回答 DNS Query，不轉送後續 HTTP Request。Browser 取得 IP 後，會直接連線至該 Data Center 的 Load Balancer。每個 Data Center 的 Load Balancer 則是 Reverse Proxy，負責在該 Data Center 內選擇 Web Server。

## GeoDNS 與 Load Balancer 的責任

| 元件 | 選擇範圍 | 是否處理 HTTP Request |
| --- | --- | --- |
| GeoDNS | Region 或 Data Center | 否，只回答 DNS Query |
| Data Center Load Balancer | Data Center 內的 Backend | 是 |

GeoDNS 與 Load Balancer 不是二選一。GeoDNS 先選 Data Center，Data Center Load Balancer 再選內部 Web Server。

## Data Center 拓樸

```text
Taipei Data Center
├-> Load Balancer 198.51.100.10:443
├-> Taipei Web Server 1 10.1.1.11:80
└-> Taipei Web Server 2 10.1.1.12:80

Virginia Data Center
├-> Load Balancer 198.51.100.20:443
├-> Virginia Web Server 1 10.2.1.11:80
└-> Virginia Web Server 2 10.2.1.12:80
```

本機模擬使用：

| 元件 | 本機位址 |
| --- | --- |
| CDN Edge | `127.0.0.1:8070` |
| Taipei Load Balancer | `127.0.0.1:8081` |
| Virginia Load Balancer | `127.0.0.1:8082` |
| Taipei Web Servers | `127.0.0.1:9101`、`127.0.0.1:9102` |
| Virginia Web Servers | `127.0.0.1:9201`、`127.0.0.1:9202` |

架構中的 Public／Private IP 只用於輸出說明，真正的 Socket 連線使用 localhost Ports。

## DNS TTL 與 Failover

GeoDNS 得知 Taipei Data Center 故障後，可以停止回傳 Taipei IP，但已保存舊 DNS Answer 的 Browser 或 DNS Resolver 不會立即知道：

```text
Taipei Data Center DOWN
-> Browser DNS Cache 尚未過期
-> Browser 仍連線 Taipei IP
-> 503 Service Unavailable

DNS TTL 到期
-> Browser 重新查詢 GeoDNS
-> GeoDNS 回傳 Virginia IP
-> Request 成功 Failover
```

因此 DNS-based Failover 受 TTL 與各層 DNS Cache 影響，不保證在故障發生後立即完成。

## Shared State 的簡化

本階段讓兩個 Data Centers 共用同一組 Session Store、Application Cache 與 Replicated Database：

```text
Taipei Web Servers ----+
                       +-> Global Session Store / Cache / Database
Virginia Web Servers --+
```

這使 Asia Browser Failover 至 Virginia 後仍能讀取原本 Session，讓 Stage 07 專注在 Data Center Routing 與 DNS TTL。真實跨區域共用資料會遇到延遲、網路分區、一致性、資料落地與 Failover 等問題，留待後續階段處理。

## 驗證順序

1. Asia Browser 查詢 GeoDNS，取得 Taipei Data Center IP。
2. `POST /login` 與 `GET /me` 分別由 Taipei 的兩台 Web Servers 處理。
3. US Browser 查詢 GeoDNS，取得 Virginia Data Center IP。
4. US Browser 的登入與 `/me` 由 Virginia Web Servers 處理。
5. 第一次靜態 Request 是 CDN Miss，下一次是 CDN Hit。
6. 模擬 Taipei Data Center 故障。
7. Asia Browser 的 DNS Cache 尚未到期，仍連線 Taipei 並收到 `503 Service Unavailable`。
8. 等待 DNS TTL 到期後重新查詢，GeoDNS 回傳 Virginia Data Center IP。
9. Asia Browser Failover 至 Virginia，並從共用 Session Store 取得原本的登入 Session。

## Response Headers

- `X-Data-Center`：實際處理 Request 的 Data Center。
- `X-Traffic-Route`：`LOCAL`、`FAILOVER` 或 `CDN`。
- `X-Served-By`：Data Center 內實際產生 Response 的 Web Server。
- `X-Session-Store`：`WRITE`、`HIT`、`MISS` 或 `BYPASS`。
- `X-CDN-Cache`：`HIT`、`MISS` 或 `EXPIRED`；動態 Request 顯示為 `BYPASS`。

## 啟動程式

```powershell
python src/stage07_multi_data_center.py
```

程式只使用 Python 標準函式庫。

## 本階段不處理

真實 DNS Server、EDNS Client Subnet、Anycast、Global Reverse Proxy、Traffic Weight、Latency-based Routing、跨資料中心 Session Replication、跨區域 Cache、Multi-Primary Database、Conflict Resolution、資料落地法規、跨區域網路分區與 CDN Multi-Origin Failover。

