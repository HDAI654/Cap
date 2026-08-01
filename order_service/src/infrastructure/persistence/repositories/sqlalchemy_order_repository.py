import logging

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.order import Order
from src.domain.ports.order_repository import OrderRepository
from src.domain.value_objects.idempotency_key import IdempotencyKey
from src.domain.value_objects.order_id import OrderId
from src.domain.value_objects.trader_id import TraderId
from src.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    DatabaseTimeoutError,
    OrderNotFoundError,
)
from src.infrastructure.persistence.mappers import model_to_order, order_to_model
from src.infrastructure.persistence.models import OrderModel

logger = logging.getLogger(__name__)


class SQLAlchemyOrderRepository(OrderRepository):
    """Persists Order aggregates using SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> None:
        logger.info("Adding order: order_id=%s", order.id.value)

        model = order_to_model(order)
        self._session.add(model)
        await self._execute_db_operation("add_order", self._session.flush)

        logger.info("Order added successfully: order_id=%s", order.id.value)

    async def get_by_id(self, order_id: OrderId) -> Order:
        logger.info("Getting order by id: order_id=%s", order_id.value)

        stmt = select(OrderModel).where(OrderModel.id == order_id.value)
        result = await self._execute_db_operation(
            "get_order_by_id",
            self._session.execute,
            stmt,
        )
        model = result.scalar_one_or_none()
        if model is None:
            logger.debug("Order not found: order_id=%s", order_id.value)
            raise OrderNotFoundError(f"Order '{order_id.value}' does not exist.")

        logger.info("Order retrieved successfully: order_id=%s", order_id.value)
        return model_to_order(model)

    async def get_by_idempotency_key(
        self,
        trader_id: TraderId,
        idempotency_key: IdempotencyKey,
    ) -> Order | None:
        logger.info(
            "Getting order by idempotency key: trader_id=%s, key=%s",
            trader_id.value,
            idempotency_key.value,
        )

        stmt = select(OrderModel).where(
            OrderModel.trader_id == trader_id.value,
            OrderModel.idempotency_key == idempotency_key.value,
        )
        result = await self._execute_db_operation(
            "get_order_by_idempotency_key",
            self._session.execute,
            stmt,
        )
        model = result.scalar_one_or_none()
        if model is None:
            logger.debug(
                "Order not found for idempotency key: trader_id=%s, key=%s",
                trader_id.value,
                idempotency_key.value,
            )
            return None

        logger.info(
            "Order retrieved by idempotency key: order_id=%s",
            model.id,
        )
        return model_to_order(model)

    async def update(self, order: Order) -> None:
        logger.info("Updating order: order_id=%s", order.id.value)

        stmt = select(OrderModel).where(OrderModel.id == order.id.value)
        result = await self._execute_db_operation(
            "get_order_by_id",
            self._session.execute,
            stmt,
        )
        model = result.scalar_one_or_none()
        if model is None:
            logger.debug("Order not found for update: order_id=%s", order.id.value)
            raise OrderNotFoundError(f"Order '{order.id.value}' does not exist.")

        if order.is_status_changed():
            model.status = order.status.value

        if order.is_fills_changed():
            model.filled_quantity = order.filled_quantity.value

        if order.is_changed():
            model.updated_at = order.updated_at

        logger.info("Order updated successfully: order_id=%s", order.id.value)

    async def list_by_trader(self, trader_id: TraderId) -> list[Order]:
        logger.info("Listing orders for trader: trader_id=%s", trader_id.value)

        stmt = (
            select(OrderModel)
            .where(OrderModel.trader_id == trader_id.value)
            .order_by(OrderModel.created_at.desc())
        )
        result = await self._execute_db_operation(
            "list_orders_by_trader",
            self._session.execute,
            stmt,
        )
        models = result.scalars().all()

        logger.info(
            "Orders listed successfully: trader_id=%s, count=%s",
            trader_id.value,
            len(models),
        )
        return [model_to_order(model) for model in models]

    async def _execute_db_operation(self, operation: str, coro, *args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except IntegrityError as e:
            logger.exception("Database integrity error during %s", operation)
            raise DatabaseOperationError(f"Database integrity error: {e}") from e
        except OperationalError as e:
            logger.exception("Database connection error during %s", operation)
            raise DatabaseConnectionError(f"Failed to connect to database: {e}") from e
        except TimeoutError as e:
            logger.exception("Database timeout during %s", operation)
            raise DatabaseTimeoutError(f"Database operation timed out: {e}") from e
        except SQLAlchemyError as e:
            logger.exception("Database error during %s", operation)
            raise DatabaseOperationError(f"Database operation failed: {e}") from e
