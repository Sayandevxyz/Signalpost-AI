import asyncio

from signalpost.app.sources.base import StaticRegistrySource
from signalpost.app.sources.website import WebsiteSource


def test_website_extraction_is_deterministic():
    extracted = asyncio.run(
        WebsiteSource().extract(
            "<html><head><title>Example AS</title></head>"
            "<body><script>ignore()</script><h1>Example AS</h1>"
            "<p>Evidence-first software.</p></body></html>"
        )
    )
    assert extracted["title"] == "Example AS"
    assert extracted["h1"] == ["Example AS"]
    assert "ignore()" not in extracted["text"]
    assert "Evidence-first software." in extracted["text"]


def test_static_registry_source_builds_targeted_query():
    result = asyncio.run(StaticRegistrySource().search("912345678"))
    assert result[0]["company_number"] == "912345678"
    assert "912345678" in result[0]["url"]
    assert result[0]["url"].startswith("https://")
