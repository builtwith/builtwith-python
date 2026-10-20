"""Framework-neutral tools. No LLM service or framework is required."""

from builtwith_official import BuiltWith, JSONValue


class WebsiteTools:
    """Bind tools to a reusable client owned by the application."""

    def __init__(self, client: BuiltWith) -> None:
        self.client = client

    def inspect_website_technologies(self, domain: str) -> JSONValue:
        """Return technologies for a root domain. Consumes BuiltWith credits."""
        return self.client.domain(domain, no_pii=True, live_only=True).data

    def validate_technology_name(self, technology: str) -> JSONValue:
        """Validate a technology name using Trends without spending API credits."""
        return self.client.trends(technology).data

    def list_registration_types(self) -> JSONValue:
        """List company registration types without a key or API credits."""
        return self.client.vat_types().data


if __name__ == "__main__":
    with BuiltWith() as client:
        # The runnable demo only invokes a public, credit-free function.
        print(WebsiteTools(client).list_registration_types())
