# Multi-Data Center

## 一句話解釋

Multi-Data Center 是將服務部署在不同故障範圍或地理區域，讓流量可以進入較合適的 Data Center，並在其中一個 Data Center 故障時切換至其他位置。

## 核心概念

- Data Center 是容納運算、網路與儲存設備的實體設施；系統架構中的 Data Center 通常代表一組能獨立承接服務流量的資源。
- 每個 Data Center 可以有自己的 Public Endpoint、Load Balancer、Web Servers、Private Network 與其他區域內服務。
- Multi-Data Center 可以降低整個區域故障造成的影響，也能讓 Client 連向網路距離較合適的位置。
- GeoDNS、Anycast 或 Global Reverse Proxy 都可能用來選擇 Data Center；Data Center 內仍可使用 Load Balancer 選擇 Backend。
- Stateless Web Tier 讓 Web Server 不保存單機專屬 Session，因此 Server 與 Data Center 之間的流量切換比較容易。
- Web Tier 無狀態不代表跨 Data Center 的資料問題已解決；Session、Cache 與 Database 仍需考慮放置位置、複寫與一致性。
- Data Center Failover 不只是改變流量目的地，還必須確保目的地有足夠容量、必要資料及可用的相依服務。
- 跨區域網路通常比同一 Data Center 內的網路延遲高，也更可能遇到網路分區。

## Active-Active 與 Active-Passive

Active-Active 讓多個 Data Centers 平時都承接流量：

```text
Asia Clients -> Taipei Data Center
US Clients   -> Virginia Data Center
```

優點是資源平時就有使用，也能讓 Client 靠近服務；但資料同步、衝突與容量規劃通常更複雜。

Active-Passive 讓主要 Data Center 平時承接流量，備援 Data Center 等待故障切換：

```text
Normal:   Clients -> Primary Data Center
Failure:  Clients -> Standby Data Center
```

設計較容易理解，但備援容量、資料新鮮度與切換程序仍需定期驗證。

Stage 07 平時讓 Asia 與 US Clients 分別使用不同 Data Center，屬於簡化的 Active-Active；Taipei 故障後，Asia Client 轉往 Virginia。

## Region、Availability Zone 與 Data Center

- Region 通常是相對獨立的地理區域。
- Availability Zone 通常是 Region 內具有獨立故障範圍的一組基礎設施。
- 實體 Data Center 是放置設備的設施；一個 Availability Zone 可能由一個或多個 Data Centers 組成。

不同 Cloud Provider 的實際定義可能不同，不能假設 Region、Availability Zone 與單棟 Data Center 永遠一一對應。

## Shared State 的挑戰

如果兩個 Data Centers 都需要處理同一位使用者，必須決定 Session 與業務資料的位置：

```text
Taipei Web Servers ----+
                       +-> Shared State
Virginia Web Servers --+
```

可能面臨：

- 跨區域讀寫延遲。
- Replication Lag。
- 同時寫入造成的 Conflict。
- Data Center 間網路中斷。
- 資料落地與法規限制。
- 故障切換後資料是否足夠新。

Stage 07 暫時使用 Global Session Store、Global Application Cache 與 Global Replicated Database，目的是先隔離並觀察 Data Center Routing 與 Failover。

## 程式對應位置

- [`DataCenter`](../src/stage07_multi_data_center.py)：描述 Region、Public IP、Load Balancer、Backends 與健康狀態。
- [`DATA_CENTERS`](../src/stage07_multi_data_center.py)：建立 Taipei 與 Virginia 兩個 Data Centers。
- [`run_data_center_load_balancer()`](../src/stage07_multi_data_center.py)：在選定的 Data Center 內以 Round Robin 分配 Request。
- [`SharedSessionStore`](../src/stage07_multi_data_center.py)：以共用物件模擬跨 Data Center 可存取的 Session Store。
- [`main()`](../src/stage07_multi_data_center.py)：展示區域路由、Taipei 故障與 Virginia Failover。

