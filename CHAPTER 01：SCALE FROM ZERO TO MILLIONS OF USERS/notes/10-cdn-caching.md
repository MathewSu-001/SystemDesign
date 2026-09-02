# CDN Caching

## 一句話解釋

CDN Caching 是以 HTTP Request 資訊建立 Cache Key，將 Origin Response 暫存在 Edge，並依 Cache Policy 決定重用、更新或略過該 Response。

## 核心概念

- Stage 05 以 `Host + Path` 建立 Cache Key，例如 `www.mysite.com/static/logo.txt`。
- Cache Key 若包含的資訊不足，可能將不同使用者或不同版本的 Response 錯誤視為相同內容。
- Stage 05 只快取 `GET /static/*`，`/profile` 與寫入操作一律 Bypass。
- Cache Hit 不會進入 Origin；Miss 和 Expired 會向 Origin 取得 Response，成功後保存至 Edge。
- CDN TTL 決定 Edge Response 可以重用多久；TTL 到期不代表內容主動推送更新，而是下一次 Request 需要重新驗證或取得。
- Origin 更新後，CDN 在 TTL 到期前可能仍回傳舊版本，形成 Stale Content。
- Cache Purge 可以主動使指定 CDN Cache 失效，但需要額外的部署與錯誤處理機制。
- Versioned URL 或 Content Hash 會在內容改變時產生新 URL，適合搭配長 TTL。
- 動態產生的公開 Response 也可能被 CDN 快取；個人資料與授權結果則預設不應進入共用 CDN Cache。
- 真實 Cache Policy 還可能使用 `Cache-Control`、Query String、Cookie、Authorization 與其他 Headers。

## 程式對應位置

- [`CDNEdgeCache.get()`](../src/stage05_cdn.py)：判斷 CDN Hit、Miss 或 Expired。
- [`CDNEdgeCache.set()`](../src/stage05_cdn.py)：保存完整 Origin HTTP Response 並設定 TTL。
- [`CDN_CACHE_TTL`](../src/stage05_cdn.py)：將教學用 CDN TTL 設定為三秒。
- [`StaticOrigin`](../src/stage05_cdn.py)：保存 `/static/logo.txt` 的 Origin 版本。
- [`StaticOrigin.deploy()`](../src/stage05_cdn.py)：模擬 Origin 從 `Logo v1` 更新為 `Logo v2`。
- [`main()`](../src/stage05_cdn.py)：展示 Miss、Hit、Origin 更新、Stale Content 與 TTL Expiration。

