class DomainValidationError(ValueError):
    """An input breaks a domain invariant. Carries the offending field name."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message
