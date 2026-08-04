import logging
from dataclasses import dataclass
from decimal import Decimal

from src.domain.events.order_events import OrderCancelled
from src.domain.ports.event_publisher import EventPublisher
from src.domain.ports.unit_of_work import UnitOfWork
from src.domain.ports.wallet_gateway import WalletGateway
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.order_side import OrderSide
from src.infrastructure.http_clients.noop_wallet_gateway import NoOpWalletGateway

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CancelOrderCommand:
    """Input for the cancel-order use case."""

    order_id: str


class CancelOrderHandler:
    """Cancel an active order, release reservations, publish OrderCancelled."""

    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        wallet_gateway: WalletGateway | None = None,
    ) -> None:
        self._uow = uow
        self._event_publisher = event_publisher
        self._wallet = wallet_gateway or NoOpWalletGateway()

    async def handle(self, command: CancelOrderCommand) -> None:
        logger.info("Cancelling order: order_id=%s", command.order_id)

        order_id = OrderId(command.order_id)
        published = False

        async with self._uow:
            order = await self._uow.orders.get_by_id(order_id)
            order.cancel()

            if order.is_changed():
                await self._uow.orders.update(order)
                await self._uow.commit()
                order.clear_changes()
                published = True

        if published:
            await self._release_reservation(order)
            await self._event_publisher.publish(
                OrderCancelled(
                    order_id=order.id.value,
                    trader_id=order.trader_id.value,
                    instrument_id=order.instrument_id.value,
                    side=order.side.value,
                    filled_quantity=order.filled_quantity.value,
                    remaining_quantity=order.remaining_quantity.value,
                )
            )

        logger.info("Order cancelled successfully: order_id=%s", command.order_id)

    async def _release_reservation(self, order) -> None:
        remaining = order.remaining_quantity.value
        if remaining <= 0:
            return

        if order.side is OrderSide.BUY and order.limit_price is not None:
            amount = order.limit_price.amount * Decimal(remaining)
            await self._wallet.release_buy_reservation(
                order.trader_id.value,
                amount,
                order.limit_price.currency.value,
            )
        elif order.side is OrderSide.SELL:
            await self._wallet.release_sell_reservation(
                order.trader_id.value,
                order.instrument_id.value,
                remaining,
            )
