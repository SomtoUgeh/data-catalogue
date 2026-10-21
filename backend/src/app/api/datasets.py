"""HTTP routes for /datasets. Each route maps a request to one service call; errors are handled in errors.py."""

from typing import Annotated, Any

from fastapi import APIRouter, Query, status

from app.api.dependencies import Service
from app.schemas import Dataset, DatasetCreate, ErrorResponse, ValidationErrorResponse

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

router = APIRouter(prefix="/datasets", tags=["datasets"])

# operation_id names the functions in the generated TypeScript client (frontend: npm run gen:api).

INVALID_REQUEST: dict[int | str, dict[str, Any]] = {400: {"model": ValidationErrorResponse}}
RATE_LIMITED: dict[int | str, dict[str, Any]] = {
    429: {
        "model": ErrorResponse,
        "description": "More than 10 writes in a minute from one IP. Deployed Worker only; see Retry-After.",
    }
}


@router.get("", operation_id="listDatasets", responses=INVALID_REQUEST)
async def list_datasets(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Page size.")] = DEFAULT_PAGE_SIZE,
    before: Annotated[
        str | None,
        Query(pattern=r"^\d+$", description="Return datasets older than this id: the last id of the previous page."),
    ] = None,
) -> list[Dataset]:
    """Lists datasets newest first. A page shorter than `limit` is the last one."""
    return await service.list_datasets(limit, int(before) if before else None)


@router.post(
    "",
    operation_id="createDataset",
    status_code=status.HTTP_201_CREATED,
    responses=INVALID_REQUEST | RATE_LIMITED,
)
async def create_dataset(data: DatasetCreate, service: Service) -> Dataset:
    """Saves the dataset after running AI curation. If curation fails, the dataset is still saved."""
    return await service.create_dataset(data)


@router.delete(
    "/{dataset_id}",
    operation_id="deleteDataset",
    responses={404: {"model": ErrorResponse}} | RATE_LIMITED,
)
async def delete_dataset(dataset_id: str, service: Service) -> Dataset:
    return await service.delete_dataset(dataset_id)
