# Load Balancer 筆記

## 兩段 TCP 連線

Load Balancer 不會把公開 IP 與 Web Server 私有 IP 合併。一次 HTTP Request 會經過兩段獨立連線：

```text
Browser -> Load Balancer public IP
Load Balancer private network -> Web Server private IP
```

Stage 02 在本機分別以 `127.0.0.1:8080` 和 `127.0.0.1:9001~9003` 表示這兩段連線。

## Server Pool 與 Health Check

Load Balancer 保存 Backend 清單，但只會從通過 Health Check 的節點中選擇。程式在每個 Request 前呼叫 `/health`：

- `200 OK`：節點可以接收 Request。
- `503 Unavailable` 或連線失敗：本次不選擇該節點。

真實系統通常會在背景定期檢查，而不是讓每個使用者 Request 等待完整 Health Check。Stage 02 採用逐次檢查，是為了讓執行輸出清楚呈現判斷過程。

## Round Robin

Round Robin 記住下一個 Backend 的位置，依序輪流分配。某個 Backend 不健康時會跳過它，但不會把它從原始 Server Pool 永久刪除，因此它恢復健康後可以再次被選中。

Round Robin 不考慮 Request 執行時間、CPU、記憶體或 Active Connections。本階段先使用這個最小策略，以聚焦理解 Load Balancer 的代理與故障排除角色。

## 程式對應位置

- [`RoundRobinLoadBalancer`](../src/stage02_load_balancer.py)：保存下一個選擇位置並跳過不健康節點。
- [`is_healthy()`](../src/stage02_load_balancer.py)：向 Backend 的 `/health` 發送 HTTP Request。
- [`proxy_request()`](../src/stage02_load_balancer.py)：建立第二條 TCP 連線並轉送 Request。
- [`run_load_balancer()`](../src/stage02_load_balancer.py)：接受外部連線、選擇 Backend 並傳回 Response。
