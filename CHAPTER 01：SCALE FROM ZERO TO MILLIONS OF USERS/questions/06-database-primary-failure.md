# Database Primary 故障時怎麼辦？

## 問題

Single-primary 架構中的 Primary 無法連線或永久故障時，系統如何恢復寫入？最新資料是否可能遺失？

## 短答案

系統會先確認 Primary 故障，再選擇資料較新的健康 Replica，將它 Promote 為新 Primary，並讓 Write Endpoint 指向新節點。若採用非同步複製，尚未傳到 Replica 的最新寫入可能遺失。自動 Failover 還必須使用 Quorum、Leader Election 或 Fencing，避免舊 Primary 與新 Primary 同時接受寫入而形成 Split Brain。

## Failover 流程

原始架構：

```text
Primary A
├-> Replica B
└-> Replica C
```

Primary A 故障後：

```text
Primary A (offline)
Primary B (原 Replica B)
└-> Replica C
```

典型步驟是：

1. 透過 Heartbeat、Connection 或查詢結果偵測 Primary 異常。
2. 使用多次檢查或多數節點判斷，避免因短暫網路問題錯誤切換。
3. 比較 Replicas 的複製進度，選擇適合提升的節點。
4. 將選中的 Replica Promote 為新 Primary。
5. 更新 Database Proxy、Service Discovery、DNS 或 Managed Endpoint，將寫入導向新 Primary。
6. 讓其他 Replicas 改為追蹤新 Primary。
7. 舊 Primary 恢復後先重新同步，再以 Replica 身分加入，不能直接恢復寫入。

## Split Brain

Primary A 可能只是與部分節點失去網路，實際上仍在運作。如果此時直接提升 Primary B，兩台節點可能同時接受寫入：

```text
Client Group 1 -> Primary A
Client Group 2 -> Primary B
```

這稱為 Split Brain。系統通常透過 Quorum、Leader Lease 與 Fencing 確保只有一台節點擁有寫入權。Fencing 的目的，是在新 Primary 接手前，確保舊 Primary 無法繼續修改共享資料。

## 資料是否會遺失？

非同步複製下可能發生：

```text
Primary 已接受 Transaction 100
Replica 只同步到 Transaction 99
Primary 永久故障
```

如果 Replica 被提升，Transaction 100 可能不存在。同步或 Quorum 複製可以降低這項風險，但會提高寫入延遲，並可能在可確認節點不足時停止寫入。

架構通常用兩個指標描述故障目標：

- RPO：可以接受遺失多少時間範圍的資料。
- RTO：故障後允許服務中斷多久。

## Stage 03 的範圍

目前程式只模擬正常狀態下的非同步複製，沒有偵測 Primary 故障、選舉新 Primary、重新路由或避免 Split Brain。這些是 Database High Availability 的下一層問題。

