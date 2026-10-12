class VictorError(Exception):
    """Error comprensible que se puede presentar al usuario."""


class Cancelled(VictorError):
    def __init__(self):
        super().__init__("Operación detenida.")


def check_cancel(event):
    if event.is_set():
        raise Cancelled()
