class TasksAPIClient:
    """Минимальный клиент API для создания проектов Яндекс Заданий."""

    def __init__(self, requester):
        self.requester = requester

    def create_project(self, payload: dict) -> dict:
        return self.requester.request(
            "POST", f"{self.requester.base_url}/projects", json=payload
        )
