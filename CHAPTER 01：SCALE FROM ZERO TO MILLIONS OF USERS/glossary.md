# Chapter 01 術語表

| 術語 | 解釋 |
|---|---|
| Client | 主動向服務發送請求的程式，例如 Web Browser 或 Mobile App。 |
| Server | 接受 Client 請求、處理請求並回傳結果的程式或機器。 |
| Domain Name | 方便人類閱讀的網路名稱，例如 `www.mysite.com`。 |
| DNS | Domain Name System，查詢網域名稱相關紀錄的分散式命名系統。 |
| DNS Resolver | 代替 Client 查詢 DNS，並將結果回傳給 Client 的服務。 |
| Authoritative DNS | 對特定 DNS Zone 的紀錄具有最終回答權的 DNS Server。 |
| DNS Record | 儲存在 DNS 中的資料，例如 A、AAAA、CNAME 與 NS Record。 |
| A Record | 將名稱對應至 IPv4 位址的 DNS Record。 |
| CNAME Record | 將一個名稱設定為另一個名稱之別名的 DNS Record。 |
| TTL | DNS 紀錄可以被快取的時間長度。 |
| IP Address | 用來識別網路介面並協助路由封包的位址。 |
| Port | 用來區分同一台機器上不同網路服務的數字。 |
| TCP | 提供可靠、有順序 Byte Stream 的傳輸層協定。 |
| TCP Three-Way Handshake | TCP 使用 SYN、SYN-ACK、ACK 建立連線的過程。 |
| Socket | 應用程式使用作業系統網路能力的程式介面。 |
| HTTP | Client 與 Server 交換 Request 和 Response 的應用層協定。 |
| HTTP Request | Client 傳給 Server 的 HTTP 訊息，包含 Method、Path、Headers，以及可選的 Body。 |
| HTTP Response | Server 傳給 Client 的 HTTP 訊息，包含 Status、Headers，以及可選的 Body。 |
| HTTP Method | 表達請求目的的動詞，例如 `GET`、`POST`、`PUT`、`DELETE`。 |
| HTTP Status Code | 表示請求處理結果的三位數代碼，例如 `200`、`404`、`500`。 |
| HTTP Header | 描述 Request 或 Response 額外資訊的欄位。 |
| HTTP Body | HTTP 訊息實際承載的內容，例如 HTML 或 JSON。 |
| HTML | 描述網頁內容與結構的標記語言。 |
| API | 讓不同軟體交換資料或呼叫功能的介面。 |
| JSON | 常用於 Web API 的結構化文字資料格式。 |
| localhost | 代表本機的主機名稱，通常對應到 `127.0.0.1`。 |

[回到 Chapter 01](./README.md)
