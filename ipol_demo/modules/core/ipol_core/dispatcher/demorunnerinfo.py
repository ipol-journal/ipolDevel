from dataclasses import dataclass


@dataclass
class DemoRunnerInfo:
    """
    Demorunner information object
    """

    name: str
    capabilities: list[str]
