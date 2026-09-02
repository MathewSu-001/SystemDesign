# 靜態與動態內容有什麼不同？CDN Bypass 又是什麼？

## 問題

靜態內容和動態內容如何區分？CDN 的 Hit、Miss、Expired 與 Bypass 分別代表什麼，為什麼 `/profile` 要 Bypass？

## 短答案

靜態內容通常在部署或上傳時產生，相同 URL 對不同 Client 回傳相同內容；動態內容則可能依使用者、時間或當前資料即時產生。但動態內容並非絕對不能快取，真正的判斷是 Response 能否安全共用以及能否接受短暫舊版本。Bypass 表示 CDN 不使用這次 Request 的 Cache，直接轉送 Origin，而且通常不保存 Response。

## 靜態與動態內容

常見靜態內容：

```text
/static/logo.png
/static/app.js
/static/style.css
/videos/demo.mp4
```

常見動態內容：

```text
/profile
/orders/123
/cart
/account/balance
```

靜態不代表永遠不更新，而是某個版本的內容在產生後通常固定。動態 Response 也可能是公開且所有人相同，例如商品介紹；若允許短暫舊資料，它仍可能由 CDN 短時間快取。

## CDN 狀態

| 狀態 | 是否使用 Cache | 是否到 Origin | 是否保存 Response |
| --- | --- | --- | --- |
| Hit | 是 | 否 | 已保存 |
| Miss | 是，但沒有 Entry | 是 | 成功時通常保存 |
| Expired | Entry 已過期 | 是 | 成功時重新保存 |
| Bypass | 否 | 是 | 通常不保存 |

Bypass 不是額外 Server，而是 CDN 對這次 Request 採取的處理方式：

```text
Browser -> CDN (BYPASS) -> Origin
```

## 為什麼 `/profile` Bypass？

`/profile` 可能依登入使用者回傳不同結果。如果 CDN 只以 Path 作為 Cache Key，可能發生：

```text
Alice GET /profile -> CDN 保存 Alice Profile
Bob GET /profile   -> 錯誤收到 Alice Profile
```

因此個人資料、Authorization Result、購物車與帳戶資訊預設不應進入共用 CDN Cache。若要快取，必須設計能區分使用者且不會洩漏資料的 Cache Policy。

## Stage 05 的選擇

Stage 05 使用簡化規則：只有 `GET /static/*` 可以進入 CDN Cache，其他 Method 與 Path 全部 Bypass。真實 CDN 還會考慮 `Cache-Control`、Cookie、Authorization、Query String 與其他設定。

