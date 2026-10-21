"""HTTP routes for /datasets. Each route maps a request to one service call; errors are handled in errors.py."""

from fastapi import APIRouter, status

from app.api.dependencies import Service
from app.schemas import Dataset, DatasetCreate, ErrorResponse, ValidationErrorResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])

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
