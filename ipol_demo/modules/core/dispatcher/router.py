from config import settings
from dispatcher import dispatcher
from fastapi import APIRouter

dispatcherRouter = APIRouter(prefix="/dispatcher")
dispatcher = dispatcher.Dispatcher(
    workload_provider=dispatcher.APIWorkloadProvider(settings.base_url),
    ping_provider=dispatcher.APIPingProvider(settings.base_url),
    demorunners=dispatcher.parse_demorunners(settings.demorunners_path),
    policy=dispatcher.make_policy(settings.policy),
)


@dispatcherRouter.get("/stats", status_code=200)
def get_demorunners_stats():
    """
    Get workload of all DRs.
    """
    return dispatcher.get_demorunners_stats()
