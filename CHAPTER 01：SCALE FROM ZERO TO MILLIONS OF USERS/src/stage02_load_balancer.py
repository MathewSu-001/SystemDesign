"""Stage 02：Load Balancer 與多台 Web Server。

預定資料流：
Browser -> DNS -> Load Balancer -> healthy Web Server -> Browser

這個檔案是 Stage 02 的獨立執行入口；後續將在此實作：
1. DNS 將網域解析至 Load Balancer 的公開 IP。
2. Load Balancer 維護 Web Server 的內網位址與健康狀態。
3. 使用 Round Robin 將請求分散至健康的 Web Server。
4. 模擬其中一台 Web Server 離線時的故障排除。
"""


def main() -> None:
    """Stage 02 的執行入口。"""
    print("Stage 02 scaffold: Load Balancer + multiple Web Servers")


if __name__ == "__main__":
    main()
