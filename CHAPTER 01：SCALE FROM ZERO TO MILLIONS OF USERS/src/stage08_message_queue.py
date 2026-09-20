"""Stage 08：以購物下單流程示範 Message Queue 與背景 Workers。"""

from __future__ import annotations

import copy
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class Message:
    message_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class Delivery:
    message: Message
    attempt: int = 1


class OrderDatabase:
    """正式訂單資料來源；Queue 不取代 Database。"""

    def __init__(self) -> None:
        self._orders: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def insert(self, order: dict[str, Any]) -> None:
        with self._lock:
            self._orders[order["order_id"]] = copy.deepcopy(order)
        print(f"[Database] INSERT order={order['order_id']}")

    def find_by_user(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [
                copy.deepcopy(order)
                for order in self._orders.values()
                if order["user_id"] == user_id
            ]


class OrderCache:
    """加速同步查詢；Cache Miss 時仍以 Database 為準。"""

    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.Lock()

    def get(self, user_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            orders = self._data.get(user_id)
            if orders is None:
                print(f"[Order Cache] MISS user={user_id}")
                return None
            print(f"[Order Cache] HIT user={user_id}")
            return copy.deepcopy(orders)

    def set(self, user_id: str, orders: list[dict[str, Any]]) -> None:
        with self._lock:
            self._data[user_id] = copy.deepcopy(orders)
        print(f"[Order Cache] SET user={user_id}")

    def invalidate(self, user_id: str) -> None:
        with self._lock:
            self._data.pop(user_id, None)
        print(f"[Order Cache] INVALIDATE user={user_id}")


class Subscription:
    def __init__(self, name: str, max_attempts: int) -> None:
        self.name = name
        self.max_attempts = max_attempts
        self.deliveries: queue.Queue[Delivery | None] = queue.Queue()
        self.dead_letters: list[Delivery] = []
        self._lock = threading.Lock()

    def move_to_dead_letter(self, delivery: Delivery) -> None:
        with self._lock:
            self.dead_letters.append(delivery)


class MessageBroker:
    """用獨立訂閱 Queue 模擬 Event Fan-out、ACK、Retry 與 DLQ。"""

    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}

    def subscribe(self, name: str, max_attempts: int = MAX_ATTEMPTS) -> Subscription:
        subscription = Subscription(name, max_attempts)
        self._subscriptions[name] = subscription
        return subscription

    def publish(self, message: Message) -> None:
        print(
            f"[Broker] PUBLISH type={message.event_type} "
            f"message={message.message_id} subscriptions={len(self._subscriptions)}"
        )
        for subscription in self._subscriptions.values():
            subscription.deliveries.put(Delivery(message))

    @staticmethod
    def ack(subscription: Subscription, delivery: Delivery) -> None:
        print(
            f"[{subscription.name}] ACK message={delivery.message.message_id} "
            f"attempt={delivery.attempt}"
        )

    @staticmethod
    def reject(subscription: Subscription, delivery: Delivery, reason: str) -> None:
        if delivery.attempt >= subscription.max_attempts:
            subscription.move_to_dead_letter(delivery)
            print(
                f"[{subscription.name}] DLQ message={delivery.message.message_id} "
                f"after={delivery.attempt} attempts reason={reason}"
            )
            return

        retried = Delivery(delivery.message, delivery.attempt + 1)
        print(
            f"[{subscription.name}] RETRY message={delivery.message.message_id} "
            f"next_attempt={retried.attempt} reason={reason}"
        )
        subscription.deliveries.put(retried)


class RetryableError(RuntimeError):
    pass


class AcknowledgementLost(RuntimeError):
    """工作已完成，但 ACK 未送達，用來示範重複投遞。"""


Handler = Callable[[Message, int], None]


class Consumer:
    def __init__(
        self,
        name: str,
        broker: MessageBroker,
        subscription: Subscription,
        handler: Handler,
    ) -> None:
        self.name = name
        self.broker = broker
        self.subscription = subscription
        self.handler = handler
        self.processed_message_ids: set[str] = set()
        self.thread = threading.Thread(target=self._run, name=name, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.subscription.deliveries.put(None)
        self.thread.join(timeout=2)

    def _run(self) -> None:
        while True:
            delivery = self.subscription.deliveries.get()
            try:
                if delivery is None:
                    return

                message = delivery.message
                print(
                    f"[{self.name}] RECEIVE message={message.message_id} "
                    f"attempt={delivery.attempt}"
                )

                if message.message_id in self.processed_message_ids:
                    print(f"[{self.name}] IDEMPOTENT SKIP message={message.message_id}")
                    self.broker.ack(self.subscription, delivery)
                    continue

                try:
                    self.handler(message, delivery.attempt)
                    self.processed_message_ids.add(message.message_id)
                    self.broker.ack(self.subscription, delivery)
                except AcknowledgementLost as error:
                    # 副作用已完成，故先記錄，再模擬 Broker 沒收到 ACK。
                    self.processed_message_ids.add(message.message_id)
                    self.broker.reject(self.subscription, delivery, str(error))
                except RetryableError as error:
                    self.broker.reject(self.subscription, delivery, str(error))
            finally:
                self.subscription.deliveries.task_done()


class CheckoutService:
    """模擬由 Load Balancer 後方的 Web Server 處理同步 HTTP Request。"""

    def __init__(
        self,
        database: OrderDatabase,
        cache: OrderCache,
        broker: MessageBroker,
    ) -> None:
        self.database = database
        self.cache = cache
        self.broker = broker

    def create_order(
        self,
        web_server: str,
        user_id: str,
        email: str,
        sku: str,
        quantity: int,
    ) -> str:
        order_id = f"order-{uuid.uuid4().hex[:8]}"
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "email": email,
            "sku": sku,
            "quantity": quantity,
            "status": "CREATED",
        }

        print(f"\n[{web_server}] POST /orders user={user_id}")
        self.database.insert(order)
        self.cache.invalidate(user_id)
        self.broker.publish(
            Message(
                message_id=f"msg-{uuid.uuid4().hex[:8]}",
                event_type="OrderCreated",
                payload=copy.deepcopy(order),
            )
        )
        print(f"[{web_server}] 201 Created order={order_id} (workers run asynchronously)")
        return order_id

    def get_orders(self, web_server: str, user_id: str) -> list[dict[str, Any]]:
        print(f"\n[{web_server}] GET /users/{user_id}/orders")
        orders = self.cache.get(user_id)
        source = "Order Cache"
        if orders is None:
            orders = self.database.find_by_user(user_id)
            self.cache.set(user_id, orders)
            source = "Database"
        print(f"[{web_server}] 200 OK source={source} orders={len(orders)}")
        return orders


def email_handler(message: Message, _attempt: int) -> None:
    email = str(message.payload["email"])
    if "@" not in email:
        raise RetryableError("email provider rejected invalid address")
    print(f"[Email Worker] SEND confirmation to={email}")


def inventory_handler(message: Message, attempt: int) -> None:
    if message.payload["user_id"] == "user-001" and attempt == 1:
        raise RetryableError("inventory service timeout")
    print(
        f"[Inventory Worker] RESERVE sku={message.payload['sku']} "
        f"quantity={message.payload['quantity']}"
    )


def analytics_handler(message: Message, attempt: int) -> None:
    print(f"[Analytics Worker] RECORD order={message.payload['order_id']}")
    if message.payload["user_id"] == "user-001" and attempt == 1:
        raise AcknowledgementLost("connection lost before ACK")


def main() -> None:
    database = OrderDatabase()
    cache = OrderCache()
    broker = MessageBroker()

    email_subscription = broker.subscribe("Email Queue")
    inventory_subscription = broker.subscribe("Inventory Queue")
    analytics_subscription = broker.subscribe("Analytics Queue")

    consumers = [
        Consumer("Email Worker", broker, email_subscription, email_handler),
        Consumer("Inventory Worker", broker, inventory_subscription, inventory_handler),
        Consumer("Analytics Worker", broker, analytics_subscription, analytics_handler),
    ]
    for consumer in consumers:
        consumer.start()

    checkout = CheckoutService(database, cache, broker)
    checkout.create_order("Web Server 1", "user-001", "alice@example.com", "BOOK", 1)
    checkout.create_order("Web Server 2", "user-002", "invalid-email", "MUG", 2)

    # 同步讀取仍走 Cache / Database，而不是從 Message Queue 取訂單。
    checkout.get_orders("Web Server 1", "user-001")
    checkout.get_orders("Web Server 2", "user-001")

    for subscription in (email_subscription, inventory_subscription, analytics_subscription):
        subscription.deliveries.join()

    print("\n[Broker] All queues drained")
    for subscription in (email_subscription, inventory_subscription, analytics_subscription):
        print(f"[{subscription.name}] DLQ depth={len(subscription.dead_letters)}")

    for consumer in consumers:
        consumer.stop()


if __name__ == "__main__":
    main()
