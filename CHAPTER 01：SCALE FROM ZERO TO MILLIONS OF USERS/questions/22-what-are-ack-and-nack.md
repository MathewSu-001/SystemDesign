# ACK 與 NACK 是什麼？

## 問題

Consumer 收到 Message 後，為什麼還要回傳 ACK？如果沒有 ACK、回傳 NACK，或 ACK 在網路中遺失，Broker 會怎麼處理？

## 短答案

ACK（Acknowledgement）表示 Consumer 已成功處理 Message，Broker 可以將它標記為完成。NACK（Negative Acknowledgement）表示處理失敗，Broker 可以依政策重新投遞、丟棄或移入 Dead Letter Queue。若 Broker 沒收到 ACK，通常會把 Message 視為未完成並再次投遞。

## ACK 的流程

```text
Broker -> Consumer：deliver Message
Consumer：execute work
Consumer -> Broker：ACK
Broker：mark Message completed
```

ACK 是 Consumer 對 Broker 的處理確認，不是 Consumer 回覆 Producer，也不是 HTTP Client 收到的 Response。

如果 Broker 一交付就刪除 Message，Consumer 可能在完成前故障：

```text
Broker -> Consumer
Broker deletes Message
Consumer crashes
```

讓 Broker 等到 ACK 才標記完成，可以在 Consumer 故障時重新投遞。

## ACK 應該何時送出？

```text
先 ACK：ACK -> execute work -> crash
後 ACK：execute work -> ACK
```

先 ACK 可能讓尚未完成的工作永久遺失。完成後 ACK 可以降低遺失風險，但 Consumer 可能收到重複 Message。Stage 08 選擇完成後 ACK，也就是 at-least-once delivery。

## NACK 與沒有 ACK

NACK 是 Consumer 明確告知 Broker「處理失敗」：

```text
Consumer -> NACK
Broker -> retry / discard / DLQ
```

沒有 ACK 可能表示 Consumer 仍在執行、Process 故障、Connection 中斷，或 ACK 在網路中遺失。Broker 通常在 Connection 關閉或 Visibility Timeout 到期後重新投遞。不同 Broker 的確認機制不完全相同。

## ACK 遺失

```text
1. Consumer 收到 msg-123
2. Consumer 成功完成工作
3. Consumer 送出 ACK
4. ACK 在網路中遺失
5. Broker 再次投遞 msg-123
```

Broker 無法知道工作已完成，只能重新投遞以避免遺失。Consumer 因此需要冪等性：

```text
收到 msg-123
-> 已處理：跳過副作用，直接 ACK
-> 未處理：執行副作用、記錄完成、ACK
```

正式系統可以使用 Database Unique Constraint、Inbox Table 或下游服務提供的 Idempotency Key；只把已處理 ID 放在 Worker 記憶體中，Process 重啟後就會遺失。

## ACK、Retry 與 DLQ

```text
成功       -> ACK -> completed
暫時失敗   -> NACK / no ACK -> retry
多次失敗   -> max attempts reached -> DLQ
```

一個 Subscription 的 ACK 只代表該 Subscription 完成。Email Worker ACK，不表示 Inventory 與 Analytics Workers 也已完成。

## Stage 08 的選擇

Stage 08 的 Consumer 先執行 Handler，成功後才呼叫 [`MessageBroker.ack()`](../src/stage08_message_queue.py)。Analytics Worker 會模擬工作完成但 ACK 遺失；重新投遞時，Consumer 以 Message ID 執行 `IDEMPOTENT SKIP`，避免重複副作用後再 ACK。
