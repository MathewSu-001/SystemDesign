# 除了 Round Robin，主流 Load Balancer 如何分配伺服器？

## 問題

除了最基礎的 Round Robin，現在常見的 Load Balancer 還會使用哪些方式分配伺服器？哪一種才算主流？

## 短答案

沒有一種演算法全面取代 Round Robin。Round Robin 仍是許多 L7 Load Balancer 的預設策略；當 Request 處理時間差異明顯時，常改用 Least Connections 或 Least Requests。Server 規格不同時可以加入 Weight；需要讓相同 Client 或資源固定到同一 Backend 時，則使用 Consistent Hashing 或 Sticky Session。L4 Load Balancer 通常依連線的 IP、Port 與 Protocol 計算 Flow Hash。

不論採用哪種分配方式，Load Balancer 都應先透過 Health Check 排除不健康的 Backend。

## 常見演算法

| 使用情境 | 常見方式 | 選擇依據 |
| --- | --- | --- |
| Server 規格相同，Request 工作量接近 | Round Robin | 依序輪流選擇 |
| Request 處理時間差異大 | Least Connections / Least Requests | 選擇進行中工作較少的 Server |
| Server 規格不同 | Weighted Round Robin / Weighted Random | 處理能力較高的 Server 接收較多流量 |
| Session、Cache Key 或相同資源需要固定 Backend | Consistent Hashing / Sticky Session | 根據 Client IP、Cookie、User ID 或其他 Key 映射 |
| L4 TCP/UDP Load Balancer | Flow Hash | 根據 Source/Destination IP、Port 與 Protocol 選擇 |

## Round Robin

Round Robin 只記住下一台 Server，依序分配：

```text
Request 1 -> Web Server 1
Request 2 -> Web Server 2
Request 3 -> Web Server 3
Request 4 -> Web Server 1
```

它容易理解且成本低，適合 Server 規格相近、Request 工作量也相近的情況。它的限制是只知道分配次數，不知道前一個 Request 是否已經完成。

Round Robin 並沒有過時。例如 AWS Application Load Balancer 的預設演算法仍是 Round Robin，Google Cloud 的 Backend Service 在未設定 Session Affinity 時也以 Round Robin 作為預設 Locality Policy。

## Least Connections 與 Least Requests

這類演算法會選擇目前工作量較少的 Server：

```text
Web Server 1：8 個 Active Requests
Web Server 2：2 個 Active Requests  <- 選擇
Web Server 3：5 個 Active Requests
```

不同產品可能稱為 Least Connections、Least Requests 或 Least Outstanding Requests。它比 Round Robin 更適合 Request 耗時差異明顯的服務，例如一般查詢只需要數毫秒，但報表或影片處理需要數秒。

有些實作不會比較全部 Server，而是隨機選出兩台，再選 Active Requests 較少的一台。這種方式稱為 Power of Two Choices，可以在較低選擇成本下得到不錯的負載分布。Google Cloud 的 `LEAST_REQUEST` 使用的便是這種做法。

## Weighted 分配

如果 Server 的硬體規格不同，可以設定權重：

```text
Web Server 1：Weight 1
Web Server 2：Weight 2
Web Server 3：Weight 4
```

Web Server 3 會取得比 Web Server 1 更多的流量。Weight 也常用於 Canary Deployment，例如讓舊版本接收 90% 流量，新版本先接收 10% 流量。

## Consistent Hashing 與 Sticky Session

某些系統希望相同 Client 或相同資源持續前往同一 Backend：

```text
hash(Session ID) -> Web Server 1
hash(User ID)    -> Web Server 3
hash(Cache Key)  -> Web Server 2
```

Consistent Hashing、Ring Hash 或 Maglev 能在 Server 增減時減少需要重新映射的 Key。Sticky Session 則常透過 Cookie 將同一使用者導向先前選中的 Backend。

這些機制能維持 Affinity，但也可能造成流量不平均。因此一般 Stateless HTTP API 不一定需要使用它們。

## L4 的 Flow Hash

L4 Load Balancer 不一定會解析 HTTP，而是根據一條 Connection 的網路資訊選擇 Backend，常見輸入包含：

```text
Source IP
Source Port
Destination IP
Destination Port
Protocol
```

同一條 TCP Connection 建立後，其封包必須持續送往同一台 Backend，否則 Backend 無法維護正確的 TCP 狀態。AWS Network Load Balancer 就使用 Flow Hash 選擇 Target。

## 內容路由與負載分配是兩件事

L7 Load Balancer 通常先根據 Host 或 Path 選擇服務：

```text
/api/users/*  -> User Service Target Group
/api/orders/* -> Order Service Target Group
/images/*     -> Image Service Target Group
```

選定 Target Group 後，才使用 Round Robin、Least Requests 等演算法選擇該群組中的一台 Server。前者決定「進入哪個服務」，後者決定「服務中由哪台 Server 處理」。

## Stage 02 的選擇

Stage 02 使用 Round Robin 搭配 Health Check，因為此階段的目標是先理解：

1. Load Balancer 如何代理兩段 TCP 連線。
2. 如何保存多台 Backend。
3. 如何依序分散 Request。
4. 如何排除離線的 Backend。

等這個流程清楚後，再將 Round Robin 替換成 Least Requests，會比較容易觀察演算法造成的差異。

## 參考資料

- [AWS：Application Load Balancer routing algorithms](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html)
- [AWS：Elastic Load Balancing request routing](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html)
- [Google Cloud：Backend services and locality policies](https://docs.cloud.google.com/load-balancing/docs/backend-service)
