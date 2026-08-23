# TCP

## 一句話解釋

TCP 是在兩個應用程式之間提供可靠、有順序 Byte Stream 的傳輸層協定。

## 核心概念

- TCP 建立連線時會執行 SYN、SYN-ACK、ACK 三向交握。
- TCP 使用 Sequence Number 維持資料順序。
- 資料遺失時，TCP 會進行重新傳送。
- 流量控制避免接收端來不及處理資料。
- 擁塞控制避免傳送端對網路注入過多資料。
- TCP 傳送的是連續 Byte Stream，不保留應用層訊息邊界。
- 應用程式透過 Socket API 使用作業系統提供的 TCP 能力，不需要自行實作 TCP。

## 程式對應位置

- [`socket.socket(AF_INET, SOCK_STREAM)`](../src/single_server_simulation.py)：建立 IPv4 TCP Socket。
- [`bind()` 與 `listen()`](../src/single_server_simulation.py)：綁定本機位址並開始監聽 TCP 連線。
- [`accept()`](../src/single_server_simulation.py)：接受已建立的 Client 連線。
- [`socket.create_connection()`](../src/single_server_simulation.py)：由 Browser 端要求建立 TCP 連線。
- [`sendall()`](../src/single_server_simulation.py)：透過 TCP 傳送完整資料。
- [`recv()`](../src/single_server_simulation.py)：從 TCP Byte Stream 讀取資料。
