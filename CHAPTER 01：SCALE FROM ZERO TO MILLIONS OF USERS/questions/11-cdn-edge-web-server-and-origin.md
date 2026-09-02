# CDN Edge Server、Web Server 與 Origin 分別是什麼？

## 問題

CDN Edge Server 和 Web Server 有什麼差別？Origin 是特定 Server、Database，還是另一種角色？靜態檔案一定存在 Database 嗎？

## 短答案

CDN Edge 主要在靠近 Client 的位置代理、快取與傳遞 HTTP Content；Web Server 主要執行 Application Logic 並產生 Response。Origin 是 CDN 在 Miss 或 Bypass 時呼叫的上游 HTTP 服務角色，可以是 Load Balancer、Web Server 或 Object Storage，通常不是 Database。靜態檔案可以存在 Database，但圖片、影片、CSS 與 JavaScript 通常更適合 File Storage 或 Object Storage。

## CDN Edge Server

CDN Edge 的主要工作包括：

- 接收 Client HTTP/HTTPS Request。
- 判斷 Response 是否可以快取。
- Cache Hit 時直接回傳。
- Cache Miss 時向 Origin 取得內容。
- 保存 Origin Response 並在後續 Request 重用。

CDN Edge 通常不負責建立訂單、更新帳戶或執行複雜 Database Transaction。部分 CDN 支援 Edge Functions，但不代表所有 Edge 都等同完整 Application Server。

## Web Server

Web Server 或 Application Server 負責：

- 驗證使用者身分與權限。
- 執行 Application Logic。
- 查詢 Shared Cache 或 Database。
- 修改正式資料。
- 呼叫其他內部服務。
- 組合 HTTP Response。

```text
POST /orders
-> 驗證使用者
-> 檢查庫存
-> 建立訂單
-> 回傳結果
```

## Origin

Origin 是從 CDN 角度定義的上游來源：

```text
CDN Miss/Bypass
-> Origin Endpoint
```

可能的 Origin 包含：

```text
CDN
├-> Load Balancer
├-> Web Server
├-> Object Storage
└-> API Gateway
```

CDN 通常透過 HTTP 向 Origin 取得 Response。Database 使用 SQL 或專用 Database Protocol，通常位於 Web Server 後方，因此 Origin 不等於 Database。

## 靜態檔案與 Database

靜態檔案技術上可以用 BLOB 存在 Database，但大型圖片、影片與建置產生的 CSS/JavaScript 通常保存於 Object Storage 或檔案系統。Database 可以只保存 Metadata：

```text
Database:
user_id = 123
avatar_url = /images/avatar-123.jpg

Object Storage:
avatar-123.jpg 的實際 Bytes
```

## Stage 05 的選擇

Stage 05 的 Origin Endpoint 是 Load Balancer，再由 Load Balancer 選擇 Web Server。`StaticOrigin` dictionary 模擬靜態內容來源，尚未加入真實 Object Storage。

