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
| GeoDNS | Authoritative DNS 根據查詢來源區域、服務健康狀態或路由政策回傳不同 DNS Answer 的功能。 |
| DNS Cache | Browser、Operating System 或 DNS Resolver 暫時保存 DNS Answer，直到 TTL 到期。 |
| DNS-Based Routing | 透過回傳不同 IP Address，將新的 Client Connection 導向不同 Region 或 Data Center 的路由方式。 |
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
| Cookie | Browser 依 Domain、Path 與其他規則保存，並在後續 HTTP Request 中傳回 Server 的小型資料。 |
| Session Cookie | 未指定持久保存期限、通常在 Browser Session 結束後移除的 Cookie；也常被泛指用來攜帶 Session ID 的登入 Cookie。 |
| Set-Cookie | Server 要求 Browser 建立或更新 Cookie 的 HTTP Response Header。 |
| Cookie Attributes | 控制 Cookie 保存、傳送與存取方式的屬性，例如 `HttpOnly`、`Secure`、`SameSite`、`Path` 與 `Max-Age`。 |
| HTML | 描述網頁內容與結構的標記語言。 |
| API | 讓不同軟體交換資料或呼叫功能的介面。 |
| Endpoint | Client 可以呼叫的具體服務入口；HTTP API 常以 Method 加 Path 表示，例如 `POST /login`。 |
| JSON | 常用於 Web API 的結構化文字資料格式。 |
| localhost | 代表本機的主機名稱，通常對應到 `127.0.0.1`。 |
| Load Balancer | 接收 Client 流量，並將 Request 分配給健康 Backend 的元件。 |
| Backend | 位於 Load Balancer 後方，實際處理 Request 的 Server。 |
| Server Pool / Target Group | 註冊在 Load Balancer 中、可供選擇的一組 Backends。不同產品使用的名稱可能不同。 |
| Reverse Proxy | 代表後方 Servers 接收 Client Request、轉送 Request，再將 Response 傳回 Client 的代理元件。 |
| Global Reverse Proxy | 接收實際 Client Connection 或 HTTP Request，再選擇 Region、Data Center 或 Backend 的全球代理層。 |
| Health Check | Load Balancer 用來判斷 Backend 是否能繼續接收流量的檢查。 |
| Round Robin | 依序輪流選擇健康 Backend 的負載分配方式。 |
| Horizontal Scaling | 透過增加 Server 數量擴充系統的整體處理能力。 |
| Single Point of Failure | 某個單一元件故障時，會導致整體服務無法運作的設計風險。 |
| Data Center | 容納運算、網路與儲存設備的實體設施；在系統架構中通常代表一組能獨立承接服務流量的資源。 |
| Multi-Data Center | 將服務部署到多個 Data Centers，以降低區域故障風險並改善不同地區 Client 的存取延遲。 |
| Region | Cloud Provider 劃分的地理區域，通常包含一個或多個彼此隔離的 Availability Zones。 |
| Availability Zone | Region 內具有獨立電力、網路或其他故障範圍的一組基礎設施。 |
| Failover | 主要服務或目的地失效時，將流量或工作切換至健康備援服務的過程。 |
| Active-Active | 多個 Data Centers 平時都承接正式流量的部署模式。 |
| Active-Passive | 主要 Data Center 平時承接流量，備援 Data Center 在故障時接手的部署模式。 |
| Global Traffic Management | 根據區域、延遲、健康狀態或容量，在多個全球 Endpoints 之間選擇流量目的地。 |
| Web Tier | 位於 Load Balancer 後方、負責處理 HTTP Request 與應用邏輯的一組 Web Servers。 |
| Stateful Server | 將跨 Request 的 Client 專屬狀態保存在單一 Server 本機，因此後續 Request 可能必須回到相同 Server。 |
| Stateless Server | 不將 Client 專屬狀態只保存在單一 Server 本機，因此 Request 可以交由不同 Server 處理。 |
| Session | Server 用來連結同一使用者多次 Request 的短期狀態，例如登入身分與到期時間。 |
| Session ID | Browser 與 Server 用來定位 Session 的不透明隨機識別碼，應難以猜測且幾乎不重複。 |
| Session Store | 讓多台 Web Servers 共用 Session 的儲存系統，可以由 Redis、Database 或其他 Key-Value Store 實作。 |
| Session Expiration | Session 超過有效期限後失效，並可由 Session Store 清除的機制。 |
| Sticky Session | Load Balancer 盡量將同一使用者的 Request 分配給相同 Backend 的路由方式。 |
| Database | 用來持久化、組織與查詢應用程式資料的系統。 |
| Primary Database | 接受資料新增、修改與刪除，並將變更複製給 Replicas 的主要資料庫節點。 |
| Database Replica | 接收 Primary 資料變更的副本節點，常用來分散讀取流量。 |
| Database Replication | 將一個資料庫節點的資料變更複製到其他節點的機制。 |
| Read/Write Splitting | 將讀取送往 Replicas、將資料變更送往 Primary 的路由方式。 |
| Replication Lag | Primary 已完成變更，但 Replica 尚未套用該變更的時間差或進度差。 |
| Eventual Consistency | 各副本可能短暫不一致，但在沒有新變更且同步正常時，最終會達到一致。 |
| Stale Read | 從落後的 Replica 讀到尚未包含最新變更的舊資料。 |
| Read-after-write Consistency | 同一個 Client 完成寫入後，後續讀取能立即看見該次寫入的保證。 |
| Cache | 將常用資料暫存在較快的儲存層，減少重複計算或 Database 查詢的元件。 |
| Shared Cache | 由多台 Web Servers 共用的獨立 Cache，例如 Redis 或 Memcached。 |
| Cache-Aside | Application 先查 Cache，Miss 時查 Database 並回填 Cache，寫入後使 Cache 失效的策略。 |
| Cache Hit | 查詢的 Key 存在於 Cache 且尚未過期，可以直接取得資料。 |
| Cache Miss | 查詢的 Key 不存在或已過期，Application 必須從其他資料來源取得資料。 |
| Cache Invalidation | 在來源資料改變後刪除或更新對應 Cache，避免繼續回傳舊資料。 |
| TTL | Time To Live，一筆 Cache 資料在自動過期前可以存活的時間。 |
| CDN | Content Delivery Network，透過分散在不同地區的 Edge Servers 快取與傳遞內容，降低 Client 延遲及 Origin 負載。 |
| Edge Server | CDN 中靠近 Client，負責接收 Request、快取並回傳內容的 Server。 |
| Edge Location | 部署一組 CDN Edge Servers 的網路節點或地理據點。 |
| Origin | CDN 在 Cache Miss、Expired 或 Bypass 時轉送 Request 的上游 HTTP 服務。 |
| Static Content | 通常在部署或上傳時產生，相同 URL 對不同 Clients 多半回傳相同結果的內容。 |
| Dynamic Content | 根據使用者、時間、Request 或目前資料即時產生的內容。 |
| Cache Key | Cache 用來識別不同內容的 Key；CDN 常依 Host、Path、Query String 與部分 Headers 組成。 |
| Cache Bypass | CDN 不使用且通常不保存這次 Request 的 Cache，而是直接將 Request 轉送至 Origin。 |
| Message Queue | 在 Producer 與 Consumer 之間暫存及傳遞工作或事件，讓 Consumer 可以非同步處理的元件。 |
| Message Broker | 接收、保存、路由及投遞 Message 的服務。 |
| Message | Producer 傳給 Consumer 的資料單位，通常包含 Message ID、類型與 Payload。 |
| Producer | 建立並發布 Message 至 Message Broker 的程式或服務。 |
| Consumer | 從 Queue 取得 Message 並執行處理邏輯的程式或服務。 |
| Worker | 執行背景工作的 Process 或 Server；在 Message Queue 架構中通常扮演 Consumer。 |
| Asynchronous Processing | Producer 提交工作後不等待工作全部完成，由其他元件稍後處理的執行方式。 |
| Event | 描述已經發生之事實的 Message，例如 `OrderCreated`。 |
| Subscription | Consumer 對某類 Message 的獨立接收管道與處理進度。 |

[回到 Chapter 01](./README.md)
