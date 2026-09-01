# Cache-Aside

## 一句話解釋

Cache-Aside 是由 Application 先查 Cache，Miss 時再查 Database 並回填 Cache，資料更新後則使 Cache 失效的快取策略。

## 核心概念

- 讀取時先查 Cache；Hit 時直接回傳，不需要查詢 Database。
- Cache Miss 時查詢 Database，取得資料後再寫入 Cache，供後續 Request 使用。
- 寫入時先更新 Database Primary，成功後刪除對應 Cache Key。
- 刪除 Cache 而不是直接更新，可以避免 Application 必須在兩個儲存系統中維護相同的寫入邏輯。
- Database 更新成功但 Cache 刪除失敗時，Cache 可能持續回傳舊資料，因此仍需要重試、監控或 TTL 等保護。
- Cache Miss 查詢落後的 Replica 時，舊資料可能被重新寫入 Cache，延長 Replication Lag 的影響。
- TTL 能限制舊 Cache 最長存活時間，但不能保證 Read-after-write Consistency。
- 需要立即看到寫入結果時，可以在短時間內讀 Primary，或只使用已追上指定複製進度的 Replica。
- 多個 Request 同時遇到相同 Cache Miss 時，可能一起查詢 Database；這類 Cache Stampede 問題不在本階段實作。

## 程式對應位置

- [`run_web_server()`](../src/stage04_cache.py)：實作 Cache-Aside 讀取以及寫入後 Cache Invalidation。
- [`SharedCache.get()`](../src/stage04_cache.py)：讀取路徑的第一個資料來源。
- [`ReplicatedDatabase.read()`](../src/stage04_cache.py)：Cache Miss 時從 Replica 取得資料。
- [`SharedCache.set()`](../src/stage04_cache.py)：將 Database 查詢結果回填至 Cache。
- [`SharedCache.delete()`](../src/stage04_cache.py)：Primary 寫入成功後刪除 `profile` Cache。
- [`main()`](../src/stage04_cache.py)：展示 Miss、Hit、Invalidation、Stale Cache 與 TTL Expiration。

