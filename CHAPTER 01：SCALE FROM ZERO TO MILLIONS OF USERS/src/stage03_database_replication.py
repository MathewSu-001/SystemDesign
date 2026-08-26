"""Stage 03：Database Primary、Replicas 與讀寫分離。

預定資料流：
Read:  Browser -> Load Balancer -> Web Server -> Database Replica
Write: Browser -> Load Balancer -> Web Server -> Database Primary
                                            -> replication -> Replica

這個檔案是 Stage 03 的獨立執行入口，並會保留 Stage 02 的完整架構。
"""


def main() -> None:
    """Stage 03 的執行入口。"""
    print("Stage 03 scaffold: Database Primary + Replicas")


if __name__ == "__main__":
    main()
