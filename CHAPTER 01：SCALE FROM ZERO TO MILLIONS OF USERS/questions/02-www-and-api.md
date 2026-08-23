# `www.mysite.com` 與 `api.mysite.com` 是否分別代表 Browser 與 Mobile App？

## 問題

`www.mysite.com` 與 `api.mysite.com` 是否分別代表 Web Browser 與 Mobile App？

## 短答案

不一定。`www` 和 `api` 通常是依照服務責任區分，不是按照 Client 類型強制區分；Web Browser 可以同時使用網站與 API，Mobile App 也能開啟網站。

## 詳細說明

`www.mysite.com` 通常提供 HTML、CSS、JavaScript 和圖片等網站資源。Web Browser 取得這些資源後解析並顯示網頁。

`api.mysite.com` 通常提供 JSON 等結構化資料或操作功能。原生 Mobile App 的畫面已包含在 App 程式內，因此通常向 API 取得資料，再由 App 自己呈現畫面。

現代 Web 應用也經常先從 `www.mysite.com` 取得前端程式，再由瀏覽器中的 JavaScript 呼叫 `api.mysite.com`。Mobile App 也可能透過 WebView、登入頁或付款頁存取 `www.mysite.com`。

```text
Web Browser ─┬→ www.mysite.com → HTML、CSS、JavaScript
             └→ api.mysite.com → JSON

Mobile App ──┬→ api.mysite.com → JSON
             └→ www.mysite.com → 選擇性網頁內容
```
