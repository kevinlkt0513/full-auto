from fastapi import APIRouter
from pydantic import BaseModel
from ..auth import CurrentUser
from ..config_writer import write_configs

router = APIRouter(prefix="/api/config", tags=["config"])


class ExportRequest(BaseModel):
    answers: dict


@router.post("/export")
def export(req: ExportRequest, user: str = CurrentUser):
    return write_configs(req.answers)
