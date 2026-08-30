# Primary 更新時為何不等待所有 Replicas 立即更新？

## 問題

Primary 收到資料變更時，為什麼不等所有 Replicas 都完成更新後，再向 Client 回覆成功？

## 短答案

Primary 可以等待 Replica，但這會把網路時間、Replica 寫入時間與故障影響加入每一次寫入。非同步複製讓 Primary 寫入完成後立即回覆，延遲和可用性較好，但 Replica 可能暫時落後，Primary 在同步前故障也可能遺失最新變更。同步、半同步與 Quorum 是資料安全、延遲和可用性之間的不同取捨。

## 非同步複製

```text
Client -> Primary 寫入
Client <- Primary 回覆成功
                 |
                 +-> 背景更新 Replicas
```

Client 不必等待 Replicas，因此寫入速度較快。某一台 Replica 變慢或暫時離線時，Primary 通常仍可接受寫入。缺點是 Replica 可能暫時找不到新資料或回傳舊值；如果 Primary 在同步完成前永久故障，最新寫入也可能沒有存在於可提升的 Replica。

## 同步複製

```text
Client -> Primary
          -> Replica 寫入
          <- Replica 確認
Client <- Primary 回覆成功
```

同步複製會在指定副本確認後才回覆 Client，可以提高已確認寫入的安全性。但 Client 必須等待額外網路與磁碟操作；如果要求所有 Replicas 確認，最慢或故障的 Replica 可能拖慢甚至阻止寫入。

跨區域同步的代價尤其明顯，因為每次寫入都必須承擔資料中心之間的網路往返時間。

## 半同步與 Quorum

系統不一定在「完全不等」和「等待全部」之間二選一。例如三個資料副本只要求其中兩個確認：

```text
Primary + 任一 Replica 確認
-> 向 Client 回覆成功
```

這能避免等待最慢的所有節點，又比完全非同步降低資料只存在於 Primary 的風險。實際保證取決於資料庫產品、確認規則與故障模型。

## Stage 03 的選擇

Stage 03 使用一秒的非同步複製延遲，刻意讓下列狀態可被觀察：

```text
Primary   = Alice v2
Replica 1 = Alice v1
Replica 2 = Alice v1
```

這個延遲是教學設定，不代表真實系統固定需要一秒。

