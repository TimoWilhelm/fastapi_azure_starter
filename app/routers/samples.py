import logging

from fastapi import APIRouter, Depends, Request, Response

from app.models.sample import Sample, SampleCreate, SampleUpdate
from app.services.sample_service import SampleService, get_sample_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=list[Sample],
)
async def get_samples(
    request: Request,
    response: Response,
    sample_service: SampleService = Depends(get_sample_service),
):
    return await sample_service.get()


@router.get(
    "/{id}",
    response_model=Sample,
)
async def get_sample_by_id(
    request: Request,
    response: Response,
    id: int,
    sample_service: SampleService = Depends(get_sample_service),
):
    return await sample_service.get_by_id(id)


@router.post(
    "/",
    response_model=Sample,
)
async def create_sample(
    request: Request,
    response: Response,
    sample: SampleCreate,
    sample_service: SampleService = Depends(get_sample_service),
    # response_model=Sample,
):
    return await sample_service.create(sample)


@router.put(
    "/{id}",
    response_model=Sample,
)
async def update_sample(
    request: Request,
    response: Response,
    id: int,
    sample: SampleUpdate,
    sample_service: SampleService = Depends(get_sample_service),
    # response_model=Sample,
):
    return await sample_service.update(id, sample)


@router.delete(
    "/{id}",
    status_code=204,
)
async def delete_sample(
    request: Request,
    response: Response,
    id: int,
    sample_service: SampleService = Depends(get_sample_service),
):
    await sample_service.delete(id)
    return Response(status_code=204)
