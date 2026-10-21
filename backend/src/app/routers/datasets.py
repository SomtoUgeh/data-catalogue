from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.schemas import Dataset, DatasetCreate, ErrorResponse, ValidationErrorResponse
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


def get_service(request: Request) -> DatasetService:
    return request.app.state.dataset_service


Service = Annotated[DatasetService, Depends(get_service)]

# operation_id names the functions in the generated TypeScript client (frontend: npm run gen:api).


@router.get("", operation_id="listDatasets")
async def list_datasets(service: Service) -> list[Dataset]:
    return await service.list_datasets()


@router.post(
    "",
    operation_id="createDataset",
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ValidationErrorResponse}},
)
async def create_dataset(data: DatasetCreate, service: Service) -> Dataset:
    """Saves the dataset after running AI curation. If curation fails, the dataset is still saved."""
    return await service.create_dataset(data)


@router.delete("/{dataset_id}", operation_id="deleteDataset", responses={404: {"model": ErrorResponse}})
async def delete_dataset(dataset_id: str, service: Service) -> Dataset:
    return await service.delete_dataset(dataset_id)
