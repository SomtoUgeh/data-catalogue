from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas import Dataset, DatasetCreate
from app.services.dataset_service import DatasetNotFoundError, DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


Service = Annotated[DatasetService, Depends(get_service)]


@router.get("")
async def list_datasets(service: Service) -> list[Dataset]:
    return await service.list_datasets()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_dataset(data: DatasetCreate, service: Service) -> Dataset:
    return await service.create_dataset(data)


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, service: Service) -> Dataset:
    try:
        return await service.delete_dataset(dataset_id)
    except DatasetNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Dataset '{dataset_id}' not found") from None
