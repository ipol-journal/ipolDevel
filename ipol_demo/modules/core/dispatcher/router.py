import configparser
import logging
import os
import re
import socket

from dispatcher import dispatcher
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseSettings


class Settings(BaseSettings):
    config_common_dir: str = (
        os.path.expanduser("~") + "/ipolDevel/ipol_demo/modules/config_common"
    )
    authorized_patterns: str = f"{config_common_dir}/authorized_patterns.conf"
    base_url: str = os.environ.get("IPOL_URL", "http://" + socket.getfqdn())

    demorunners_path = (
        os.path.expanduser("~")
        + "/ipolDevel/ipol_demo/modules/config_common/demorunners.xml"
    )

    policy: str = "lowest_workload"

    dispatcher = dispatcher.Dispatcher(
        workload_provider=dispatcher.APIWorkloadProvider(base_url),
        ping_provider=dispatcher.APIPingProvider(base_url),
        demorunners=dispatcher.parse_demorunners(demorunners_path),
        policy=dispatcher.make_policy(policy),
    )


settings = Settings()
dispatcherRouter = APIRouter(prefix="/dispatcher")


def validate_ip(request: Request) -> bool:
    # Check if the request is coming from an allowed IP address
    patterns = []
    ip = request.headers["x-real-ip"]
    # try:
    for pattern in read_authorized_patterns():
        patterns.append(
            re.compile(pattern.replace(".", "\\.").replace("*", "[0-9a-zA-Z]+"))
        )
    for pattern in patterns:
        if pattern.match(ip) is not None:
            return True
    raise HTTPException(status_code=403, detail="IP not allowed")


def read_authorized_patterns() -> list:
    """
    Read from the IPs conf file
    """
    # Check if the config file exists
    authorized_patterns_path = os.path.join(
        settings.config_common_dir, settings.authorized_patterns
    )
    if not os.path.isfile(authorized_patterns_path):
        logger.exception(
            f"read_authorized_patterns: \
                      File {authorized_patterns_path} doesn't exist"
        )
        return []

    # Read config file
    try:
        cfg = configparser.ConfigParser()
        cfg.read([authorized_patterns_path])
        patterns = []
        for item in cfg.items("Patterns"):
            patterns.append(item[1])
        return patterns
    except configparser.Error:
        logger.exception(f"Bad format in {authorized_patterns_path}")
        return []


def init_logging():
    """
    Initialize the error logs of the module.
    """
    logger = logging.getLogger("core")

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s; [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


@dispatcherRouter.get("/stats", status_code=200)
def get_demorunners_stats():
    """
    Get workload of all DRs.
    """
    return settings.dispatcher.get_demorunners_stats()


logger = init_logging()
