import httpx

from src.domain.ports.instrument_gateway import InstrumentGateway
from src.exceptions import InstrumentNotTradableError


class HttpInstrumentGateway(InstrumentGateway):
    """Reads instrument status from Admin Service."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout

    async def ensure_tradable(self, instrument_id: str) -> None:
        url = f"{self._base}/api/v1/instruments/{instrument_id}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url)
        except Exception as exc:
            raise InstrumentNotTradableError(
                f"Failed to load instrument '{instrument_id}': {exc}"
            ) from exc

        if response.status_code == 404:
            raise InstrumentNotTradableError(
                f"Instrument '{instrument_id}' does not exist."
            )
        if response.status_code >= 400:
            raise InstrumentNotTradableError(
                f"Instrument lookup failed ({response.status_code})."
            )

        status = response.json().get("status")
        if status != "ACTIVE":
            raise InstrumentNotTradableError(
                f"Instrument '{instrument_id}' is not tradable (status={status})."
            )
