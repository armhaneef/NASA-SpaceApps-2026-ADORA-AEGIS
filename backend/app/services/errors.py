"""Expected service failures translated into HTTP responses by the app."""


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class MLUnavailableError(Exception):
    pass


class MLResponseError(Exception):
    pass


class AssistantUnavailableError(Exception):
    pass


class AssistantResponseError(Exception):
    pass


class AssistantTimeoutError(Exception):
    pass
