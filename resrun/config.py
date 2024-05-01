from os import PathLike
from typing import TypeAlias

from pydantic import BaseModel


class ResrunBaseRepoConfig(BaseModel):
    path: str
    type: str = "local"
    id: str
    default: bool = False


class ResrunBaseTaskConfig(BaseModel):
    # TODO: Use validators to prevent type conflicts
    task: str = "backup"
    repo: str = "_default"
    path: str | list[str]
    exclude_file: str | None = None


class ResrunForgetTaskConfig(ResrunBaseTaskConfig):
    path: str | None = None
    keep_last: int | None = None
    keep_hourly: int | None = None
    keep_daily: int | None = None
    keep_weekly: int | None = None
    keep_monthly: int | None = None
    keep_yearly: int | None = None


class ResrunCopyTaskConfig(ResrunBaseTaskConfig):
    copy_to: str
    path: str | None = None
    host: str | None = None
    snapshots: list[str] | None = None


class ResrunManualTaskConfig(ResrunBaseTaskConfig):
    repo: str | None = None
    path: str | None = None
    command: str


ResrunTasks: TypeAlias = (
    ResrunBaseTaskConfig
    | ResrunCopyTaskConfig
    | ResrunForgetTaskConfig
    | ResrunManualTaskConfig
)


class ResrunBaseConfig(BaseModel):
    verbose: bool = True
    envfile: bool = True
    output_logs: bool = True

    dont_run: bool = False
    exclude_file: str | PathLike | None = None
    hostname: str | None = None
    order: list[str] = ["backup", "forget", "copy", "manual"]

    repos: list[ResrunBaseRepoConfig]
    tasks: list[ResrunTasks]
