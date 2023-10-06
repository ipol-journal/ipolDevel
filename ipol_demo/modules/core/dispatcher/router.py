from config import settings
from fastapi import APIRouter

dispatcherRouter = APIRouter(prefix="/dispatcher")


@dispatcherRouter.get("/stats", status_code=200)
def get_demorunners_stats():
    """
    Get workload of all DRs.
    """
    return settings.dispatcher.get_demorunners_stats()
