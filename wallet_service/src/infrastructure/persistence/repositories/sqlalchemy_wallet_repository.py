from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.domain.entities.wallet import Wallet
from src.domain.ports.wallet_repository import WalletRepository
from src.domain.value_objects.currency import Currency
from src.domain.value_objects.instrument_id import InstrumentId
from src.domain.value_objects.trader_id import TraderId
from src.domain.value_objects.wallet_id import WalletId
from src.exceptions import WalletNotFoundError
from src.infrastructure.persistence.mappers import (
    cash_balance_to_model,
    holding_to_model,
    model_to_wallet,
    wallet_to_model,
)
from src.infrastructure.persistence.models.wallet import (
    CashBalanceModel,
    HoldingModel,
    WalletModel,
)


class SQLAlchemyWalletRepository(WalletRepository):
    """Persists Wallet aggregates using SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, wallet: Wallet) -> None:
        model = wallet_to_model(wallet)
        self._session.add(model)

    async def get_by_id(self, wallet_id: WalletId) -> Wallet:
        model = await self._load_by_id(wallet_id.value)
        if model is None:
            raise WalletNotFoundError(f"Wallet '{wallet_id.value}' does not exist.")
        return model_to_wallet(model)

    async def get_by_trader_id(self, trader_id: TraderId) -> Wallet:
        stmt = (
            select(WalletModel)
            .where(WalletModel.trader_id == trader_id.value)
            .options(
                selectinload(WalletModel.cash_balances),
                selectinload(WalletModel.holdings),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise WalletNotFoundError(
                f"Wallet for trader '{trader_id.value}' does not exist."
            )
        return model_to_wallet(model)

    async def update(self, wallet: Wallet) -> None:
        model = await self._load_by_id(wallet.id.value)
        if model is None:
            raise WalletNotFoundError(f"Wallet '{wallet.id.value}' does not exist.")

        if wallet.is_status_changed():
            model.status = wallet.status.value

        created_cash, updated_cash = wallet.get_cash_changes()
        await self._apply_cash_changes(model, wallet, created_cash, updated_cash)

        created_holdings, updated_holdings, removed_holdings = (
            wallet.get_holding_changes()
        )
        await self._apply_holding_changes(
            model,
            wallet,
            created_holdings,
            updated_holdings,
            removed_holdings,
        )

    async def delete(self, wallet_id: WalletId) -> None:
        model = await self._session.get(WalletModel, wallet_id.value)
        if model is None:
            raise WalletNotFoundError(f"Wallet '{wallet_id.value}' does not exist.")
        await self._session.delete(model)

    async def exists_by_trader_id(self, trader_id: TraderId) -> bool:
        stmt = select(WalletModel.id).where(WalletModel.trader_id == trader_id.value)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _load_by_id(self, wallet_id: str) -> WalletModel | None:
        stmt = (
            select(WalletModel)
            .where(WalletModel.id == wallet_id)
            .options(
                selectinload(WalletModel.cash_balances),
                selectinload(WalletModel.holdings),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _apply_cash_changes(
        self,
        model: WalletModel,
        wallet: Wallet,
        created: set[Currency],
        updated: set[Currency],
    ) -> None:
        cash_by_currency = {cb.currency: cb for cb in model.cash_balances}

        for currency in created:
            balance = next(b for b in wallet.cash_balances if b.currency == currency)
            model.cash_balances.append(cash_balance_to_model(wallet.id.value, balance))

        for currency in updated:
            balance = next(b for b in wallet.cash_balances if b.currency == currency)
            existing = cash_by_currency.get(currency.value)
            if existing is None:
                model.cash_balances.append(
                    cash_balance_to_model(wallet.id.value, balance)
                )
            else:
                existing.available = balance.available.amount
                existing.reserved = balance.reserved.amount

    async def _apply_holding_changes(
        self,
        model: WalletModel,
        wallet: Wallet,
        created: set[InstrumentId],
        updated: set[InstrumentId],
        removed: set[InstrumentId],
    ) -> None:
        holdings_by_id = {h.instrument_id: h for h in model.holdings}

        for instrument_id in removed:
            existing = holdings_by_id.get(instrument_id.value)
            if existing is not None:
                await self._session.delete(existing)
                model.holdings.remove(existing)

        for instrument_id in created:
            holding = next(
                h for h in wallet.holdings if h.instrument_id == instrument_id
            )
            model.holdings.append(holding_to_model(wallet.id.value, holding))

        for instrument_id in updated:
            holding = next(
                h for h in wallet.holdings if h.instrument_id == instrument_id
            )
            existing = holdings_by_id.get(instrument_id.value)
            if existing is None:
                model.holdings.append(holding_to_model(wallet.id.value, holding))
            else:
                existing.available = holding.available.value
                existing.reserved = holding.reserved.value
                existing.average_cost = holding.average_cost.amount
                existing.average_cost_currency = holding.average_cost.currency.value
