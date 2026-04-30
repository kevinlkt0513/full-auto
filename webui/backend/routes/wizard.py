import json
from fastapi import APIRouter
from pydantic import BaseModel
from ..auth import CurrentUser
from ..settings import get_data_dir

router = APIRouter(prefix="/api/wizard", tags=["wizard"])


class WizardState(BaseModel):
    current_step: int = 1
    answers: dict = {}


def _state_path():
    return get_data_dir() / "webui_wizard_state.json"


def _read() -> WizardState:
    p = _state_path()
    if not p.exists():
        return WizardState()
    try:
        return WizardState(**json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        return WizardState()


def _write(state: WizardState) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(state.model_dump_json(indent=2), encoding="utf-8")


@router.get("/state")
def get_state(user: str = CurrentUser):
    return _read()


@router.post("/state")
def set_state(state: WizardState, user: str = CurrentUser):
    _write(state)
    return {"ok": True}
