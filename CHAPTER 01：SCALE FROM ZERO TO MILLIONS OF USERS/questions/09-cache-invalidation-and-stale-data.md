# Database 更新後，Cache 應該更新還是刪除？

## 問題

Application 更新 Database 後，應該直接更新 Cache，還是刪除 Cache 等下一次讀取回填？為什麼 Cache 中仍可能出現舊資料？

## 短答案

Cache-Aside 常採用「先更新 Database，成功後刪除 Cache」。刪除比直接更新簡單，下一次讀取會從資料來源重新建立 Cache；但 Database 更新與 Cache 刪除不是同一個原子操作，刪除失敗或並行 Request 都可能留下舊資料。若 Cache Miss 又讀到落後的 Replica，舊值還可能被重新放入 Cache。

## 為什麼刪除而不是直接更新？

一項 Database 寫入可能影響多個查詢結果：

```text
更新 user:123
可能影響：
- user:123
- users:active
- team:7:members
- search:alice
```

Application 若直接更新所有 Cache，必須正確重建每一種衍生結果。刪除受影響的 Keys，讓下一次讀取依正式資料重新計算，通常比較容易維護。

此外，有些被更新的資料短時間內不會再被讀取。直接更新 Cache 可能完成沒有使用者會命中的額外工作；刪除則只會在下一次真正需要時回填。

## 操作順序

Stage 04 使用：

```text
1. UPDATE Database Primary
2. DELETE Cache Key
```

如果先刪除 Cache 再更新 Database，可能發生：

```text
Thread A：DELETE Cache
Thread B：Cache MISS -> 讀取 Database 舊值 -> SET 舊值
Thread A：UPDATE Database 新值
```

最後 Database 是新值，但 Cache 又保存舊值。因此 Cache-Aside 常把 Database 更新放在前面。不過「更新 Database 後刪除 Cache」也不是完全無競爭；正式系統仍可能需要重試、事件通知、版本控制或其他一致性策略。

## Replication Lag 與 Stale Cache

Stage 04 刻意展示：

```text
Primary 更新 Alice v2
-> Cache DELETE
-> 立即 GET
-> Cache MISS
-> Replica 尚為 Alice v1
-> Cache SET Alice v1
```

Replica 稍後即使更新成 `Alice v2`，Cache 仍可能在 TTL 到期前回傳 `Alice v1`。Cache 因此把原本短暫的 Replication Lag 延長成 Cache Entry 的存活時間。

改善方式可以包括：

- 寫入後一段時間內讓相同 Client 讀 Primary。
- Cache Miss 時只選擇已追上指定複製進度的 Replica。
- 縮短敏感資料的 TTL。
- 使用資料版本，拒絕以較舊版本覆蓋 Cache。
- Replication 完成後再次使相關 Cache Keys 失效。

## Cache 刪除失敗

Database 更新成功後，Cache 服務可能暫時無法連線。Application 可以依需求採取重試、將 Invalidation Event 放入可靠 Queue、記錄監控告警，並以 TTL 限制舊資料存活時間。

這些機制仍無法讓 Cache 與 Database 自動成為單一 Transaction。系統必須根據資料的重要性決定可以接受多久的不一致。

## Stage 04 的選擇

Stage 04 實作「更新 Primary 後刪除 Cache」，並使用兩秒 TTL 展示舊資料最後會被刷新。Cache 刪除失敗重試、版本檢查與強 Read-after-write Consistency 暫時不處理。

