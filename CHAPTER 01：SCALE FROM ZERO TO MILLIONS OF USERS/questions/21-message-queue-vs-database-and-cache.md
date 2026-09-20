# Message Queue、Database 與 Cache 有什麼不同？

## 問題

Web Server 都是在呼叫另一個元件，為什麼取得資料使用 Database 或 Cache，傳遞工作或事件使用 Message Queue？它們可以互相取代嗎？

## 短答案

Database 保存正式狀態，Cache 加速常用資料的存取，Message Queue 則在 Producer 與 Consumer 之間傳遞工作或事件。三者解決不同問題，經常在同一個 Request 中一起使用，通常不能互相取代。

## 三者的責任

| 元件 | 主要用途 | 下單範例 |
| --- | --- | --- |
| Database | 永久保存與查詢正式資料 | 保存訂單 |
| Cache | 更快取得常用資料 | 快取訂單查詢結果 |
| Message Queue | 非同步傳遞工作或事件 | 發布 `OrderCreated` |

## 同一個 Request 同時使用三者

```text
Client -> POST /orders -> Web Server
                            |-> Database：INSERT order
                            |-> Cache：INVALIDATE user orders
                            `-> Queue：PUBLISH OrderCreated

Client <- 201 Created
```

Database 寫入成功是回覆 `201 Created` 的必要條件，因此 Web Server 必須等待。寄信不必阻塞 HTTP Response，可以透過 Queue 交給 Email Worker 稍後處理。

Client 查詢訂單時則回到 Cache 或 Database：

```text
GET /orders/order-123
-> Cache
-> Cache Miss
-> Database
```

## 為什麼 Queue 不能取代 Database？

Queue 主要負責傳遞，Message 被 ACK 後可能移除，也不一定支援依使用者或訂單條件查詢。`OrderCreated` 只能表示事件已發布，正式訂單仍應保存在 Database。

## 「是否即時」不是唯一判斷方式

真正的判斷問題是：本次 HTTP Response 是否必須取得結果？

- 必須取得：通常同步查詢或呼叫 Database、Cache 或其他服務。
- 不必取得且允許稍後完成：可以考慮 Message Queue。

登入驗證必須立即知道結果，不能先回覆成功再慢慢驗證；寄送歡迎信通常可以在背景完成。

Web Server 成功 Publish 也只表示 Broker 接受 Message，不代表 Consumer 已執行完成：

```text
PUBLISHED != PROCESSED
```

如果 Client 必須知道背景工作進度，系統通常還要將 `PENDING`、`PROCESSING`、`COMPLETED` 或 `FAILED` 狀態保存在 Database。

## Stage 08 的選擇

Stage 08 使用 Database 作為訂單的正式資料來源、Cache 加速訂單讀取，再以 Message Broker 將 `OrderCreated` 交給 Email、Inventory 與 Analytics Consumers，示範三者如何合作。
