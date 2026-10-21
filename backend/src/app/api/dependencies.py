from typing import Annotated

from fastapi import Depends, Request

from app.services.datasets import DatasetService


def get_service(request: Request) -> DatasetService:
    """Returns the service wired at startup. The Worker overrides this dependency per request."""
    return request.app.state.dataset_service


Service = Annotated[DatasetService, Depends(get_service)]
