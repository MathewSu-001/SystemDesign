# GeoDNS 和 Reverse Proxy 功能接近，所以只需要選一個嗎？

## 問題

GeoDNS 和 Reverse Proxy 都能決定流量要去哪裡，是否代表架構只要選擇其中一個，不需要同時存在？

## 短答案

不一定。兩者都能影響流量目的地，但工作階段與可見資訊不同。GeoDNS 在連線建立前透過 DNS Answer 選擇 Region 或 Data Center；Reverse Proxy 收到實際 Connection 或 HTTP Request 後才選擇 Backend。常見架構會先由 GeoDNS 選 Data Center，再由其中的 Load Balancer／Reverse Proxy 選 Web Server。

## GeoDNS 的工作

```text
Browser -> GeoDNS: www.mysite.com 在哪裡？
Browser <- GeoDNS: 198.51.100.10

Browser -> 198.51.100.10
```

GeoDNS：

- 處理 DNS Query。
- 通常選擇 Region 或 Data Center。
- 回傳 IP Address 與 TTL。
- 通常看不到後續 HTTP Method、Path、Headers、Cookie 或 Body。
- 不轉送 Browser 後續的 HTTP Request。

## Reverse Proxy 的工作

```text
Browser -> Reverse Proxy -> Backend
Browser <- Reverse Proxy <- Backend
```

Reverse Proxy：

- 位於實際流量路徑中。
- 接收並轉送 Request。
- Layer 7 Reverse Proxy 可以讀取 Host、Path、Headers 與 Cookie。
- 可以進行 TLS Termination、Authentication、Rate Limiting 或 Cache。
- 可以依 Request 內容選擇 Service 或 Backend。

## 常見的合作方式

```text
GeoDNS
  |
  | 選擇 Taipei Data Center
  v
Taipei Load Balancer / Reverse Proxy
  |
  | 選擇 Taipei Web Server
  v
Web Server
```

| 元件 | 主要決策 |
| --- | --- |
| GeoDNS | 選擇 Region／Data Center |
| Data Center Load Balancer | 選擇 Data Center 內的 Backend |

小型單區域系統可能只有 Load Balancer，不需要 GeoDNS；只使用 Global Reverse Proxy 的系統也可能不靠 GeoDNS 選 Data Center。因此是否同時使用取決於架構需求，不是固定二選一。

## Stage 07 的選擇

Stage 07 使用 GeoDNS 選擇 Taipei 或 Virginia Data Center。Browser 取得 IP 後直接連線到該 Data Center 的 Load Balancer；Load Balancer 再以 Reverse Proxy 方式將 HTTP Request 轉送給該區的 Web Server。

Stage 07 沒有新增 Global Reverse Proxy，避免把 DNS-based Routing 與 Request Proxy Routing 混在同一階段。

