from lib.api_client import TasksAPIClient
from lib.data_loader import make_project_payload


def create_project(
    requester,
    data_dir,
    public_name="Bbox: выделение бабочек",
) -> dict:
    """Создает проект по файлам задания и возвращает ответ API."""
    client = TasksAPIClient(requester)
    project = client.create_project(
        make_project_payload(data_dir, public_name=public_name)
    )
    print(f"Проект создан: {project.get('id', '<без ID в ответе API>')}")
    return project
