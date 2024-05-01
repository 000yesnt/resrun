from os import PathLike
from typing import TypeAlias, Any

from pydantic import BaseModel, model_validator, PrivateAttr


class ResrunBaseRepoConfig(BaseModel):
    path: str
    type: str = "local"
    id: str
    default: bool = False


class ResrunBaseTaskConfig(BaseModel):
    _task: str = PrivateAttr("backup")
    task: str = "backup"
    repo: str = "_default"
    path: str | list[str]
    exclude_file: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_task(cls, data: Any):
        if isinstance(data, dict):
            assert (
                data.get("task") or "backup"
            ) == cls._task.default, f"Not a {cls._task} task"
        return data


class ResrunForgetTaskConfig(ResrunBaseTaskConfig):
    _task: str = PrivateAttr("forget")
    path: str | None = None
    keep_last: int | None = None
    keep_hourly: int | None = None
    keep_daily: int | None = None
    keep_weekly: int | None = None
    keep_monthly: int | None = None
    keep_yearly: int | None = None
    # TODO: keep-within and keep-within-*; keep-tag


class ResrunCopyTaskConfig(ResrunBaseTaskConfig):
    _task: str = PrivateAttr("copy")
    copy_to: str
    path: str | None = None
    host: str | None = None
    snapshots: list[str] | None = None


class ResrunManualTaskConfig(ResrunBaseTaskConfig):
    _task: str = PrivateAttr("manual")
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
