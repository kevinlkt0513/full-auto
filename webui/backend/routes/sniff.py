import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from ..auth import CurrentUser
from ..preflight import stripe_sniff

router = APIRouter(prefix="/api/sniff", tags=["sniff"])


@router.get("/stripe")
def stripe(user: str = CurrentUser):
    def gen():
        for msg in stripe_sniff.run_sniff():
            yield {"event": msg["event"], "data": json.dumps(msg["data"])}
    return EventSourceResponse(gen())
