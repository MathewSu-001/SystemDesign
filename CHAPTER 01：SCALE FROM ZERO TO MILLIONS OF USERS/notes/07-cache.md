# Cache

## 一句話解釋

Cache 是將常用資料暫存在速度較快的儲存層，減少重複計算或 Database 查詢的元件。

## 核心概念

- Cache 通常保存可以從 Database 或其他來源重新取得的資料，不應被視為唯一正式資料來源。
- Cache Hit 表示 Key 存在且尚未過期，可以直接取得資料；Cache Miss 表示必須查詢其他資料來源。
- Local Cache 位於單一 Web Server 的記憶體內，存取速度快，但不同 Web Servers 的內容可能不一致。
- Shared Cache 是所有 Web Servers 共用的獨立服務，常見實作包含 Redis 與 Memcached。
- Shared Cache 讓一台 Web Server 寫入的 Cache 可以被其他 Web Servers 使用，有利於維持 Stateless Web Server。
- TTL 決定 Cache Entry 可以存活多久；到期後，下一次讀取會視為 Cache Miss。
- Cache Invalidation 是在來源資料改變後刪除或更新對應 Cache，避免持續回傳舊資料。
- Cache 應該被視為可失效的加速層；Cache 無法使用時，系統通常需要回到 Database 或採取降級策略。
- Cache 可以降低 Database 讀取負載，但也會增加資料一致性、容量與故障處理的複雜度。

## 程式對應位置

- [`CacheEntry`](../src/stage04_cache.py)：保存 Cache Value 與過期時間。
- [`SharedCache`](../src/stage04_cache.py)：以 Thread-safe dictionary 模擬所有 Web Servers 共用的 Cache。
- [`SharedCache.get()`](../src/stage04_cache.py)：判斷 Cache Hit、Miss 或 Expired。
- [`SharedCache.set()`](../src/stage04_cache.py)：寫入 Value 並設定 TTL。
- [`SharedCache.delete()`](../src/stage04_cache.py)：在 Database 更新後使 Cache 失效。
- [`CACHE_TTL`](../src/stage04_cache.py)：將本階段的 Cache 存活時間設定為兩秒。

