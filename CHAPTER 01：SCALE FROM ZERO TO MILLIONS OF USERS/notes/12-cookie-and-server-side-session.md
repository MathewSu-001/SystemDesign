# Cookie 與 Server-Side Session

## 一句話解釋

Browser 使用 Cookie 攜帶不透明的 Session ID，Web Server 再用該 ID 從 Shared Session Store 取得少量、短期的使用者狀態。

## 核心概念

- Cookie 是 Browser 依 Domain、Path 與其他規則保存，並在後續 HTTP Request 中傳回 Server 的小型資料。
- Server 使用 `Set-Cookie` Response Header 要求 Browser 保存 Cookie；Browser 後續使用 `Cookie` Request Header 傳送它。
- Server-side Session 通常只讓 Browser 保存 `session_id`，真正的 `user_id`、到期時間等資料留在 Session Store。
- Session ID 應該是不透明、難以猜測且幾乎不重複的隨機值，不能使用容易預測的流水號。
- Cookie 不會自行查詢 Session Store；Web Server 讀取 Cookie 後，才以 Session ID 作為 Key 查詢。
- Session 適合保存登入身分與少量短期流程狀態，不適合保存完整 HTML、圖片、大量訂單或其他大型業務資料。
- Session 必須設定 TTL，避免使用者關閉 Browser 而沒有登出時，資料永遠留在 Session Store。
- 登出時應刪除 Server-side Session，並讓 Browser 的 Session Cookie 失效。
- 重新登入或權限提升後應更換 Session ID，降低 Session Fixation 的風險。

## HTTP 傳遞流程

登入成功時，Server 建立 Session：

```text
Shared Session Store:
MOUb718z... -> {
    user_id: user-42,
    expires_at: ...
}
```

Server 回傳 Cookie：

```http
HTTP/1.1 200 OK
Set-Cookie: session_id=MOUb718z...; Path=/; HttpOnly; SameSite=Lax
```

Browser 後續自動帶上 Cookie：

```http
GET /me HTTP/1.1
Host: www.mysite.com
Cookie: session_id=MOUb718z...
```

Web Server 使用 Session ID 查詢：

```text
MOUb718z... -> user-42
```

## Cookie 安全屬性

| 屬性 | 用途 |
| --- | --- |
| `HttpOnly` | 阻止前端 JavaScript 直接讀取 Cookie，降低部分 Session 竊取風險 |
| `Secure` | 只透過 HTTPS 傳送 Cookie |
| `SameSite` | 限制跨網站 Request 攜帶 Cookie，降低 CSRF 風險 |
| `Path` | 限制哪些 URL Path 可以收到 Cookie |
| `Max-Age` / `Expires` | 設定 Browser 保存 Cookie 的期限 |

Stage 06 是未使用 TLS 的 localhost 教學程式，因此示範 `HttpOnly` 與 `SameSite=Lax`；正式 HTTPS 環境還應加入 `Secure`。

## Session 容量

Session Store 的概略容量可以估算為：

```text
平均 Session 大小 × 有效 Session 數量 × 副本數
```

實際用量還包含 Key、資料結構、記憶體碎片與系統 Metadata。控制方式包括：

- Session 只保存必要的小型資料。
- 使用 TTL 自動刪除過期 Session。
- 登出時主動刪除。
- 限制每位使用者可同時存在的 Session 數量。
- 監控 Session 數量、記憶體、Eviction、Hit Rate 與查詢延遲。
- 單一節點不足時使用 Replication、Partitioning 或 Cluster。

## 程式對應位置

- [`Session`](../src/stage06_stateless_web_tier.py)：保存 `user_id` 與 `expires_at`。
- [`SharedSessionStore.create()`](../src/stage06_stateless_web_tier.py)：使用安全隨機值建立 Session ID 並設定 TTL。
- [`SharedSessionStore.get()`](../src/stage06_stateless_web_tier.py)：判斷 Session Hit、Miss 或 Expired。
- [`get_session_id()`](../src/stage06_stateless_web_tier.py)：從 HTTP Cookie 取出 `session_id`。
- [`Browser`](../src/stage06_stateless_web_tier.py)：模擬 Browser 保存 `Set-Cookie` 並在後續 Request 傳送 Cookie。
- [`SESSION_TTL`](../src/stage06_stateless_web_tier.py)：設定教學用 Session 有效期限。

