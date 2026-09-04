# Endpoint 是什麼？

## 問題

新增需要登入的 Endpoint 是什麼意思？Endpoint 是一台 Server、一個 IP、一個 Port，還是一個網址？

## 短答案

Endpoint 是系統提供給 Client 呼叫的具體功能入口。在 HTTP API 中，通常由 Protocol、Domain、Port、HTTP Method 與 Path 共同定位；討論應用功能時，最常用 `Method + Path` 表示，例如 `POST /login` 與 `GET /me`。

## Endpoint 的組成

完整 Request Target 可以是：

```text
https://www.mysite.com:443/me
```

其中包括：

- Protocol：`https`
- Domain：`www.mysite.com`
- Port：`443`
- Path：`/me`
- HTTP Method：例如 `GET`

因此可以將 Endpoint 寫成：

```text
GET https://www.mysite.com/me
```

在相同服務的文件中，通常簡寫為：

```text
GET /me
```

## Method 也是 Endpoint 語意的一部分

相同 Path 搭配不同 Method，可以代表不同操作：

```text
GET  /profile -> 讀取 Profile
POST /profile -> 建立或寫入 Profile
PUT  /profile -> 更新 Profile
```

因此不能只看 `/profile`，還要一起看 HTTP Method。

## Endpoint 不等於實體 Server

Client 呼叫：

```text
GET /me
```

Request 實際可能經過：

```text
Browser -> CDN -> Load Balancer -> Web Server 1、2 或 3
```

三台 Web Servers 都可以提供相同的 `/me` Endpoint。Endpoint 描述對外功能與呼叫方式，不代表它永遠綁定某一台機器。

## Stage 06 的 Endpoint

```text
POST /login -> 建立 Session，Response 回傳 Set-Cookie
GET  /me    -> 從 Cookie 取得 Session ID，查詢目前登入者
```

兩者都是個人化動態操作，因此經過 CDN 時採用 Bypass，不進入共用 CDN Cache。

