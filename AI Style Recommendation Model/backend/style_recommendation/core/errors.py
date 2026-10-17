"""Workflow errors independent of the HTTP transport."""


class InferenceError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass
