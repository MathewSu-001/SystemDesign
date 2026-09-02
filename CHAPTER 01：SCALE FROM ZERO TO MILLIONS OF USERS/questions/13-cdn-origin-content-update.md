# Origin 更新後，CDN 如何取得新內容？

## 問題

靜態內容也會更新；當 Origin 已經部署新版本時，CDN 為什麼仍可能回傳舊內容，又可以如何讓 Edge 取得新版本？

## 短答案

CDN Cache 是 Origin Response 的獨立副本，Origin 更新不會自動修改所有 Edge Entries。CDN 可以等待 TTL 到期後重新向 Origin 取得內容，也可以主動 Purge Cache。對 CSS、JavaScript 與圖片等部署資源，常見做法是使用包含版本或 Content Hash 的 URL，讓新內容使用全新的 Cache Key。

## TTL

```text
CDN SET Logo v1, TTL 3 seconds
Origin 更新為 Logo v2
CDN TTL 尚未到期 -> HIT Logo v1
CDN TTL 到期     -> Origin -> Logo v2
```

TTL 能限制舊內容保存時間，但 TTL 越短，CDN 越常回到 Origin；TTL 越長，Hit Rate 越高，但舊版本可能存在較久。

## Cache Purge

部署完成後，可以要求 CDN 使指定 URL 失效：

```text
Purge /static/logo.png
```

下一次 Request 會重新向 Origin 取得內容。Purge 適合 URL 不能改變的資源，但需要處理 API 失敗、傳播時間與大量 URL 的操作成本。

## Versioned URL

內容改變時改用新 URL：

```text
/static/app.v1.js
/static/app.v2.js
```

更常見的是加入 Content Hash：

```text
/static/app.a81f2c.js
/static/app.b739de.js
```

新 URL 形成新的 Cache Key，因此不會命中舊版本。舊 URL 可以設定很長的 TTL，已載入舊 HTML 的 Client 仍能取得對應舊檔。

## 哪一種方式適合？

```text
內容檔名可以改變
-> Versioned URL / Content Hash

URL 必須保持不變
-> TTL + Cache Purge

短時間舊內容可接受
-> 依更新頻率設定 TTL
```

正式系統常同時使用版本化資源與 Purge，而不是只依賴單一方式。

## Stage 05 的選擇

Stage 05 不實作 Purge 或 Versioned URL，而是將 Origin 從 `Logo v1` 更新為 `Logo v2`，刻意展示 TTL 到期前的 CDN Hit 仍回傳舊版本，以及到期後重新向 Origin 取得新版本。

