# Session Cookie 和廣告 Cookie 有什麼不同？

## 問題

登入時使用的 Session Cookie，和網站詢問是否接受的廣告 Cookie 是同一種東西嗎？為什麼兩者都叫 Cookie？

## 短答案

兩者使用相同的 HTTP Cookie 技術，但用途不同。Session Cookie 通常讓目前網站維持登入或購物流程；廣告 Cookie 則用來識別 Browser、分析行為或投放廣告。Cookie 同意視窗主要處理隱私與資料用途，不是在定義另一種網路協定。

## 相同之處

兩者都可能透過 `Set-Cookie` 保存：

```http
Set-Cookie: session_id=abc123
Set-Cookie: advertising_id=xyz789
```

Browser 會依 Cookie 的 Domain、Path、有效期限、SameSite 與其他屬性，決定何時在 Request 中帶上 Cookie。

Cookie 名稱本身不保證用途。真正的差異在於誰設定、傳給誰、保存多久，以及 Server 如何使用其中的識別碼。

## 用途比較

| 項目 | Session Cookie | 廣告 Cookie |
| --- | --- | --- |
| 主要用途 | 維持登入與必要操作狀態 | 分析瀏覽行為與廣告投放 |
| 常見內容 | 隨機 `session_id` | Browser 或廣告識別碼 |
| 使用範圍 | 通常是目前網站 | 可能由第三方服務在多個網站使用 |
| 保存期限 | 登出、閒置或期限到達後失效 | 可能保存較長時間 |
| 網站功能 | 登入功能通常需要 | 核心登入功能通常不需要 |

## First-Party 與 Third-Party

使用者造訪：

```text
shop.example.com
```

由 `shop.example.com` 設定並傳回該網站的 Cookie，通常稱為 First-Party Cookie。若頁面載入 `ads.example.net` 的內容，而 Cookie 屬於 `ads.example.net`，則它處於 Third-Party Context。

廣告追蹤不必然只使用 Third-Party Cookie，First-Party Cookie 也可能用於分析或廣告；因此不能只靠 First-Party／Third-Party 判斷用途。

## Cookie 同意視窗

網站顯示「接受 Cookie」通常是在說明或取得分析、個人化、廣告等資料處理用途的選擇。使用者拒絕非必要廣告 Cookie，不必然代表網站不能使用維持登入、安全或購物車所需的必要 Cookie。

實際是否需要同意，以及如何分類必要或非必要 Cookie，仍取決於網站行為與適用規範；技術分類不能取代法律判斷。

## Stage 06 的 Cookie

Stage 06 的 `session_id` 是 First-Party、登入用途的模擬 Cookie：

```http
Set-Cookie: session_id=...; Path=/; HttpOnly; SameSite=Lax
```

它的工作只是讓 Browser 在後續 Request 帶回 Session ID，不用於廣告或跨網站追蹤。

