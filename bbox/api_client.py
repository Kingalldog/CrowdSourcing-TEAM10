from request import Requester

class TasksAPIClient:
    """Клиент для работы с API Яндекс.Заданий."""

    def __init__(self, requester):
        self.requester = requester

    def create_project(self, payload: dict) -> dict:
        return self.requester.request(
            "POST", f"{self.requester.base_url}/projects", json=payload
        )

    def create_pool(self, payload: dict) -> dict:
        return self.requester.request(
            "POST", f"{self.requester.base_url}/pools", json=payload
        )

    def create_training(self, payload: dict) -> dict:
        return self.requester.request(
            "POST", f"{self.requester.base_url}/trainings", json=payload
        )

    def open_training(self, training_id: str) -> dict:
        return self.requester.request(
            "POST", f"{self.requester.base_url}/trainings/{training_id}/open"
        )

    def create_tasks_async(self, tasks_payload: list[dict]) -> dict:
        return self.requester.request(
            "POST",
            f"{self.requester.base_url}/tasks",
            params={"async_mode": "true"},
            json=tasks_payload,
        )

    def get_operation(self, operation_id: str) -> dict:
        return self.requester.request(
            "GET", f"{self.requester.base_url}/operations/{operation_id}"
        )

    def get_operation_log(self, operation_id: str) -> list[dict]:
        return self.requester.request(
            "GET", f"{self.requester.base_url}/operations/{operation_id}/log"
        )

    def get_pool(self, pool_id: str) -> dict:
        """Получает полную спецификацию (свойства) пула по его ID."""
        return self.requester.request(
            "GET", f"{self.requester.base_url}/pools/{pool_id}"
        )

    def create_pool_from_spec(self, payload) -> dict:
        """
        Создаёт новый пул по выгруженной спецификации.
        Overrides: project_id, private_name, will_expire,
                   training_pool_id, training_passing_skill_value,
                   drop_training_requirement.
        """
        payload = payload
        return self.create_pool(payload)