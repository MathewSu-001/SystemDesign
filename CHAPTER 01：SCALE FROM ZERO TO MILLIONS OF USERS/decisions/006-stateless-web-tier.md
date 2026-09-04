# 006：加入無狀態 Web Tier

## 狀態

已採用。

## 問題

Stage 05 已有三台 Web Servers，但尚未示範登入 Session。如果 Session 只保存在處理登入的 Web Server 記憶體中，Load Balancer 將下一個 Request 分配給另一台 Web Server 時，另一台機器無法辨識使用者。這會迫使系統依賴 Sticky Session，也使 Web Server 不容易自由增加、移除或替換。

## 改動

- 保留 CDN Edge、Origin Load Balancer、三台 Web Servers、Shared Application Cache 與 Database Replication。
- 新增所有 Web Servers 共用的 Shared Session Store。
- 新增 `POST /login`，建立隨機且難以猜測的 `session_id`。
- Browser 只在 Cookie 保存 `session_id`；使用者登入狀態保存在 Shared Session Store。
- 新增 `GET /me`，任意 Web Server 都能用 Cookie 中的 `session_id` 查詢登入狀態。
- Web Server 本身不保存 Session，因此不需要 Sticky Session。

Session 仍然是狀態；「無狀態」指 Web Tier 的個別 Web Server 不擁有只存在於本機的使用者狀態。

## Request 流程

```text
Login:
Browser -> CDN BYPASS -> Origin Load Balancer -> Web Server 1
                                             -> Shared Session Store WRITE
Browser <- Set-Cookie: session_id=...

Authenticated request:
Browser + Cookie -> CDN BYPASS -> Origin Load Balancer -> Web Server 2 or 3
                                                      -> Shared Session Store READ
```

因為 Session Store 是共用元件，登入可以由 Web Server 1 處理，後續的 `/me` 即使由 Web Server 2 或 Web Server 3 處理也能成功。

## Cookie 與 Session 的分工

```text
Browser Cookie:
session_id=<隨機識別碼>

Shared Session Store:
<隨機識別碼> -> user_id + expires_at
```

Cookie 只攜帶查詢 Session 的編號，不保存完整 Profile、訂單或畫面。程式使用 `secrets.token_urlsafe(24)` 產生不易重複且難以猜測的 Session ID。

本機範例的 Cookie 使用 `HttpOnly` 與 `SameSite=Lax`。正式 HTTPS 環境還應加入 `Secure`。

## Session Store 與 Application Cache

| 元件 | 保存內容 | 主要用途 | 到期後結果 |
| --- | --- | --- | --- |
| Shared Session Store | `session_id -> user_id` | 辨識登入使用者 | 使用者需重新登入 |
| Shared Application Cache | Database 查詢結果 | 降低 Database 讀取量 | 回到 Database 查詢 |
| CDN Edge Cache | 完整靜態 HTTP Response | 降低 Origin 流量 | 回到 Origin 查詢 |

三者都能使用 TTL，但保存的資料、直接呼叫者與 Cache Miss 的意義不同。

## 本機模擬位址

| 元件 | 架構位址 | 本機模擬 |
| --- | --- | --- |
| CDN Edge | `203.0.113.10:443` | `127.0.0.1:8070` |
| Origin Load Balancer | `15.125.23.214:80` | `127.0.0.1:8080` |
| Web Server 1 | `10.0.1.11:80` | `127.0.0.1:9001` |
| Web Server 2 | `10.0.1.12:80` | `127.0.0.1:9002` |
| Web Server 3 | `10.0.1.13:80` | `127.0.0.1:9003` |

Shared Session Store、Shared Application Cache 與 Database 在這個單檔教學程式中以共用物件模擬，沒有另外監聽網路 Port。

## Endpoint 與 CDN 規則

```text
POST /login       -> CDN BYPASS -> 建立 Session 並回傳 Set-Cookie
GET  /me          -> CDN BYPASS -> 讀取 Cookie 並查詢 Session Store
GET  /static/*    -> CDN Cacheable
GET  /profile     -> CDN BYPASS -> Shared Application Cache / Database
POST /profile     -> CDN BYPASS -> Database Primary
```

登入與個人化 Response 不可存入本階段的 CDN Cache，避免把某位使用者的內容回傳給其他使用者。

## 驗證順序

1. 執行 Stage 05 原有的 Profile、Application Cache 與 CDN 流程。
2. `POST /login` 由 Web Server 1 處理，Shared Session Store 建立 Session。
3. Browser 從 `Set-Cookie` 保存 `session_id`。
4. 第一個 `GET /me` 由 Web Server 2 處理，從 Shared Session Store 找到相同 Session。
5. 第二個 `GET /me` 由 Web Server 3 處理，仍能辨識相同使用者。
6. Anonymous Browser 不帶 Cookie 呼叫 `/me`，得到 `401 Unauthorized`。
7. 靜態內容仍能顯示 CDN `MISS`、`HIT` 與 `EXPIRED`。

觀察輸出中的 `X-Served-By`，可確認登入與後續 Request 由不同 Web Servers 處理；`X-Session-Store` 則顯示 `WRITE`、`HIT`、`MISS` 或 `BYPASS`。

## 啟動程式

```powershell
python src/stage06_stateless_web_tier.py
```

程式只使用 Python 標準函式庫。

## 本階段不處理

真實 Redis 或 Database Session Store、密碼驗證、Session Rotation、登出、滑動式到期、Session Store Replication、Sharding、容量淘汰策略、OAuth、JWT、CSRF 完整防護、TLS、Sticky Session 與多區域部署。
