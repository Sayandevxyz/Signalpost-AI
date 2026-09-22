from typing import Any


class RegistryAgent:
    def extract(self, payload: dict[str, Any], source_url: str) -> dict[str, Any]:
        return {"company_number": str(payload.get("organizationNumber") or payload.get("company_number") or ""), "legal_name": payload.get("name") or payload.get("legal_name"), "status": payload.get("status"), "address": payload.get("address"), "organization_type": payload.get("organizationForm") or payload.get("organization_type"), "source_url": source_url}
