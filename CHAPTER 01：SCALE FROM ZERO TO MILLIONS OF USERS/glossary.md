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
| Public IP | 可以在公開網際網路上路由的 IP Address；Stage 02 的 Client 透過 Load Balancer 的 Public IP 進入系統。 |
| Private IP | 用於私有網路內部通訊、不直接在公開網際網路上路由的 IP Address。 |
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
| Load Balancer | 接收 Client 流量，並將 Request 分配給健康 Backend 的元件。 |
| Backend | 位於 Load Balancer 後方，實際處理 Request 的 Server。 |
| Server Pool / Target Group | 註冊在 Load Balancer 中、可供選擇的一組 Backends。不同產品使用的名稱可能不同。 |
| Reverse Proxy | 代表後方 Servers 接收 Client Request、轉送 Request，再將 Response 傳回 Client 的代理元件。 |
| Health Check | Load Balancer 用來判斷 Backend 是否能繼續接收流量的檢查。 |
| Round Robin | 依序輪流選擇健康 Backend 的負載分配方式。 |
| Horizontal Scaling | 透過增加 Server 數量擴充系統的整體處理能力。 |
| Single Point of Failure | 某個單一元件故障時，會導致整體服務無法運作的設計風險。 |
| Stateless Server | 不將 Client 專屬狀態只保存在單一 Server 本機，因此 Request 可以交由不同 Server 處理。 |
| Database | 用來持久化、組織與查詢應用程式資料的系統。 |
| Primary Database | 接受資料新增、修改與刪除，並將變更複製給 Replicas 的主要資料庫節點。 |
| Database Replica | 接收 Primary 資料變更的副本節點，常用來分散讀取流量。 |
| Database Replication | 將一個資料庫節點的資料變更複製到其他節點的機制。 |
| Read/Write Splitting | 將讀取送往 Replicas、將資料變更送往 Primary 的路由方式。 |
| Replication Lag | Primary 已完成變更，但 Replica 尚未套用該變更的時間差或進度差。 |
| Eventual Consistency | 各副本可能短暫不一致，但在沒有新變更且同步正常時，最終會達到一致。 |
| Stale Read | 從落後的 Replica 讀到尚未包含最新變更的舊資料。 |
| Read-after-write Consistency | 同一個 Client 完成寫入後，後續讀取能立即看見該次寫入的保證。 |

[回到 Chapter 01](./README.md)
