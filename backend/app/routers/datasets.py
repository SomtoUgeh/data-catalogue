from fastapi import APIRouter, Request, status

from app.schemas import Dataset, DatasetCreate

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _service(request: Request):
    return request.app.state.service


@router.get("", response_model=list[Dataset])
def list_datasets(request: Request) -> list[Dataset]:
    return _service(request).list_datasets()


@router.post("", response_model=Dataset, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, request: Request) -> Dataset:
    return _service(request).create_dataset(payload)


@router.delete("/{dataset_id}", response_model=Dataset)
def delete_dataset(dataset_id: str, request: Request) -> Dataset:
    return _service(request).delete_dataset(dataset_id)
