from resrun.config import (
    ResrunBaseConfig,
    ResrunBaseRepoConfig,
    ResrunBaseTaskConfig,
    ResrunCopyTaskConfig,
    ResrunTasks,
)

import tomllib
from collections import defaultdict
from pathlib import Path


class ResrunBuilder:
    _config: ResrunBaseConfig
    config_loaded: bool = False
    repos: dict[str, ResrunBaseRepoConfig] = {}
    tasks: dict[str, list[ResrunTasks]] = defaultdict(list)

    def __init__(self): ...

    def load_config(self, config: dict):
        self._config = ResrunBaseConfig.model_validate(config)
        if not self._config.repos:
            raise ValueError("No repositories in config!")
        if not self._config.tasks:
            raise ValueError("No tasks in config!")

        for repo in self._config.repos:
            if repo.default:
                if "_default" in self.repos:
                    # implies there's 2 defaults in the config
                    raise Exception("More than one default present!")
                self.repos["_default"] = repo
                continue
            self.repos[repo.id] = repo

        for task in self._config.tasks:
            self.tasks[task.task].append(task)

        self.config_loaded = True

    def load_config_file(self, filename: str):
        with open(filename, "rb") as f:
            self.load_config(tomllib.load(f))

    def build(self) -> list[str]:
        if not self.config_loaded:
            raise RuntimeError("Tried to start build before loading a config!")

        commands = []

        for task_type in self._config.order:
            for task in self.tasks[task_type]:
                match task.task:
                    case "backup":
                        commands.append(self._build_backup_task(task))
                    case "copy":
                        commands.append(self._build_copy_task(task))

        return commands

    def _get_repo_or_default(self, repo_id: str) -> ResrunBaseRepoConfig | None:
        if repo_id in self.repos:
            return self.repos[repo_id]
        elif "_default" in self.repos:
            return self.repos["_default"]

        return None

    def _build_backup_task(self, task: ResrunBaseTaskConfig) -> str:
        prefix = []
        suffix = []

        target_repo = self._get_repo_or_default(task.repo)

        if not target_repo:
            raise ValueError("Trying to backup to unknown repo!")

        # prefixes
        if self._config.verbose:
            prefix.append("-v")

        # suffixes
        _exclude_file = task.exclude_file or self._config.exclude_file or None
        if _exclude_file:
            suffix.append(f'--exclude-file="{Path(_exclude_file)}"')

        final = (
            ["restic", "-r", f'"{str(Path(target_repo.path))}"']
            + prefix
            + ["backup", f'"{str(Path(task.path))}"']
            + suffix
        )

        return " ".join(final)

    def _build_copy_task(self, task: ResrunCopyTaskConfig):
        prefix = []
        suffix = []

        source_repo = self._get_repo_or_default(task.repo)
        target_repo = self.repos.get(task.copy_to)

        if not source_repo or not target_repo:
            raise ValueError("Trying to copy from/to an unknown repo!")

        # prefixes
        if self._config.verbose:
            prefix.append("-v")

        # copying specific snapshots ignores every other param
        if task.snapshots:
            suffix.append(" ".join(task.snapshots))
        else:
            # TODO brain not braining rn
            ...

        final = (
            ["restic", "-r", f'"{str(Path(target_repo.path))}"']
            + prefix
            + ["copy", "--from-repo", f'"{str(Path(source_repo.path))}"']
            + suffix
        )

        return " ".join(final)
