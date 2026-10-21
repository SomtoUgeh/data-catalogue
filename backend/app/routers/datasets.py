from fastapi import APIRouter, Request, status

from app.schemas import Dataset, DatasetCreate, ErrorResponse, ValidationErrorResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])

VALIDATION_ERROR = {
    400: {
        "model": ValidationErrorResponse,
        "description": "Name or description is missing or blank.",
        "content": {
            "application/json": {
                "examples": {
                    "missingName": {
                        "value": {
                            "error": "Validation failed",
                            "fields": [{"field": "name", "message": "name is required"}],
                        }
                    },
                    "blankName": {
                        "value": {
                            "error": "Validation failed",
                            "fields": [{"field": "name", "message": "name is required"}],
                        }
                    },
                }
            }
        },
    },
}

NOT_FOUND_ERROR = {
    404: {
        "model": ErrorResponse,
        "description": "No dataset with that id.",
        "content": {
            "application/json": {
                "example": {"error": "Dataset with id 'missing' was not found."},
            }
        },
    },
}


def _service(request: Request):
    return request.app.state.service


@router.get(
    "",
    response_model=list[Dataset],
    operation_id="listDatasets",
    summary="List datasets",
    response_description="Every registered dataset, including the three seeded rows.",
)
def list_datasets(request: Request) -> list[Dataset]:
    return _service(request).list_datasets()


@router.post(
    "",
    response_model=Dataset,
    status_code=status.HTTP_201_CREATED,
    operation_id="createDataset",
    summary="Register a dataset",
    response_description="The saved row, with curator tags and a one-sentence summary.",
    responses=VALIDATION_ERROR,
)
def create_dataset(payload: DatasetCreate, request: Request) -> Dataset:
    return _service(request).create_dataset(payload)


@router.delete(
    "/{dataset_id}",
    response_model=Dataset,
    operation_id="deleteDataset",
    summary="Delete a dataset",
    response_description="The deleted row.",
    responses=NOT_FOUND_ERROR,
)
def delete_dataset(dataset_id: str, request: Request) -> Dataset:
    return _service(request).delete_dataset(dataset_id)
