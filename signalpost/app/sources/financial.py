from typing import Any

import httpx


class FinancialSource:
    name = "financial_data"

    async def search(self, company_number: str) -> list[dict[str, Any]]:
        """Search for financial data sources."""
        return [
            {
                "url": f"https://data.brreg.no/enhetsregisteret/api/enheter/{company_number}",
                "source": "official_registry",
                "type": "registry_financial"
            }
        ]

    async def fetch(self, url: str) -> str:
        """Fetch financial data."""
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                if len(response.content) > 2_000_000:
                    raise ValueError("financial response exceeds maximum size")
                return response.text
            except Exception as e:
                raise ValueError(f"Failed to fetch financial data: {e}")

    async def extract(self, content: str) -> dict[str, Any]:
        """Extract financial information from JSON response."""
        import json
        try:
            data = json.loads(content)
            return {
                "employees": data.get("antallAnsatte"),
                "establishment_date": data.get("stiftelsesdato"),
                "organization_form": data.get("organisasjonsform"),
            }
        except Exception:
            return {}
