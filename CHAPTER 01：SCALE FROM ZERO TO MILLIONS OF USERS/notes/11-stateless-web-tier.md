# Stateless Web Tier

## 一句話解釋

Stateless Web Tier 是讓每台 Web Server 不保存只屬於本機的使用者狀態，任何 Request 都能由任一台健康的 Web Server 處理。

## 核心概念

- 無狀態不代表整個系統沒有狀態，而是個別 Web Server 不擁有只存在於自己記憶體中的使用者狀態。
- Session、Profile 與訂單仍然存在，只是保存在所有 Web Servers 都能存取的 Shared Store 或 Database。
- 如果 Session 只存在 Web Server 1，下一個 Request 被分配到 Web Server 2 時，Web Server 2 無法辨識使用者。
- Sticky Session 可以讓同一位使用者盡量回到同一台 Web Server，但會增加 Load Balancer 與 Server 擴縮、替換、故障轉移的限制。
- 將 Session 移到 Shared Session Store 後，Load Balancer 可以使用 Round Robin 將 Request 分配給任一台 Web Server。
- Stateless Web Servers 較容易水平擴展；新 Server 啟動後不需要先取得其他 Server 的本機 Session。
- Server 故障或部署重啟時，使用者狀態不會因該 Server 的記憶體消失而立即遺失。
- Request 執行期間的區域變數可以存在 Web Server 記憶體；不能依賴的是跨 Request、只存在特定 Server 的狀態。

## Stateful 與 Stateless Request

Stateful Web Server：

```text
POST /login -> Web Server 1
               └-> Local Memory: session abc -> user-42

GET /me    -> Web Server 2
               └-> 找不到 session abc
```

Stateless Web Tier：

```text
POST /login -> Web Server 1 -> Shared Session Store: WRITE

GET /me    -> Web Server 2 -> Shared Session Store: HIT
GET /me    -> Web Server 3 -> Shared Session Store: HIT
```

## 適合與不適合放在 Web Server 本機的資料

適合只存在單次 Request 期間：

- 解析完成的 Request。
- 函式區域變數。
- 組合中的 Response。
- 可以隨時重新建立、遺失後不影響正確性的暫時資料。

不應只保存在某台 Web Server：

- 登入 Session。
- 使用者購物車的正式狀態。
- 訂單與付款狀態。
- 必須跨 Request 保存的工作進度。
- 其他 Server 必須能讀取的使用者資料。

## 程式對應位置

- [`SharedSessionStore`](../src/stage06_stateless_web_tier.py)：集中保存所有 Web Servers 共用的登入 Session。
- [`run_web_server()`](../src/stage06_stateless_web_tier.py)：每台 Web Server 執行相同邏輯，不保存自己的 Session dictionary。
- [`run_load_balancer()`](../src/stage06_stateless_web_tier.py)：以 Round Robin 將 Request 分配給不同 Web Servers。
- [`POST /login`](../src/stage06_stateless_web_tier.py)：建立 Session，即使由 Web Server 1 處理也不綁定 Web Server 1。
- [`GET /me`](../src/stage06_stateless_web_tier.py)：任意 Web Server 都能從 Shared Session Store 取得登入身分。
- [`main()`](../src/stage06_stateless_web_tier.py)：刻意讓登入與後續 Request 落到不同 Web Servers，驗證 Web Tier 無狀態。

