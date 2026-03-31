class DomainError(Exception):
    """Base class for domain errors"""

    pass


class InvalidReport(DomainError):
    pass


class InsufficientStock(DomainError):
    pass
