class InMemoryAudit:
    def __init__(self, fail: bool = False):
        self.events: list[dict] = []
        self.fail = fail

    def record(self, event):
        if self.fail:
            raise RuntimeError("audit unavailable")
        self.events.append(event)
