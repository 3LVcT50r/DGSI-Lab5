"""Service for communicating with the provider app."""

import httpx
from typing import List, Dict, Any
from src.config import Settings


class ProviderService:
    """Handles HTTP communication with the provider app."""

    def __init__(self, settings: Settings):
        self.base_url = settings.provider_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_catalog(self) -> List[Dict[str, Any]]:
        """Fetch the product catalog from provider."""
        url = f"{self.base_url}/api/v1/catalog"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def place_order(
        self,
        product_id: int = None,
        quantity: float = 0,
        product_name: str = None,
    ) -> Dict[str, Any]:
        """Place an order with the provider, by name (preferred) or id.

        Factory and provider have independent product IDs, so callers that
        cross the boundary should pass `product_name`.
        """
        url = f"{self.base_url}/api/v1/orders"
        data: Dict[str, Any] = {"quantity": quantity}
        if product_name is not None:
            data["product_name"] = product_name
        else:
            data["product_id"] = product_id
        response = await self.client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def get_orders(self, status: str = None) -> List[Dict[str, Any]]:
        """Get orders from provider, optionally filtered by status."""
        url = f"{self.base_url}/api/v1/orders"
        params = {}
        if status:
            params["status"] = status
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get a specific order from provider."""
        url = f"{self.base_url}/api/v1/orders/{order_id}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def advance_day(self) -> Dict[str, Any]:
        """Advance the day in provider app."""
        url = f"{self.base_url}/api/v1/day/advance"
        response = await self.client.post(url)
        response.raise_for_status()
        return response.json()

    async def get_current_day(self) -> Dict[str, Any]:
        """Get current day from provider."""
        url = f"{self.base_url}/api/v1/day/current"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()


# Global instance
_provider_service = None


def get_provider_service(settings: Settings) -> ProviderService:
    """Get the global provider service instance."""
    global _provider_service
    if _provider_service is None:
        _provider_service = ProviderService(settings)
    return _provider_service