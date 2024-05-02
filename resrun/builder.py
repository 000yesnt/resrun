from resrun.config import (
    ResrunBaseConfig,
    ResrunBaseRepoConfig,
    ResrunBaseTaskConfig,
    ResrunCopyTaskConfig,
    ResrunForgetTaskConfig,
    ResrunManualTaskConfig,
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
        self.repos = {}
        self.tasks = defaultdict(list)
        self._config = ResrunBaseConfig.model_validate(config)
        if not self._config.repos:
            raise ValueError("No repositories in config!")
        if not self._config.tasks:
            raise ValueError("No tasks in config!")

        for repo in self._config.repos:
            if repo.default:
                if "_default" in self.repos:
                    # implies there's 2 defaults in the config
                    raise ValueError("More than one default present!")
                self.repos["_default"] = repo
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
                        commands += self._build_backup_task(task)
                    case "copy":
                        commands.append(self._build_copy_task(task))
                    case "manual":
                        commands.append(self._build_manual_task(task))
                    case "forget":
                        commands.append(self._build_forget_task(task))

        return commands

    def _get_repo_or_default(self, repo_id: str) -> ResrunBaseRepoConfig | None:
        if repo_id in self.repos:
            return self.repos[repo_id]
        elif "_default" in self.repos:
            return self.repos["_default"]

        return None

    def _get_global_prefixes(self) -> list[str]:
        if not self.config_loaded:
            raise RuntimeError("Tried to get global prefixes without a loaded config!")
        prefix = []
        if self._config.verbose:
            prefix.append("-v")
        return prefix

    def _string_or_null(self, *args) -> str | None:
        if any([not bool(a) for a in args]):
            return None
        else:
            return "".join(map(str, args))

    def _build_backup_task(self, task: ResrunBaseTaskConfig) -> list[str]:
        prefix = self._get_global_prefixes()
        suffix = []

        target_repo = self._get_repo_or_default(task.repo)

        if not target_repo:
            raise ValueError("Trying to backup to unknown repo!")

        # suffixes
        _exclude_file = task.exclude_file or self._config.exclude_file or None
        if _exclude_file:
            suffix.append(f'--exclude-file="{Path(_exclude_file)}"')

        if isinstance(task.path, list):
            commandlist = []
            for p in task.path:
                command = (
                    ["restic", "-r", f'"{str(Path(target_repo.path))}"']
                    + prefix
                    + ["backup", f'"{str(Path(p))}"']
                    + suffix
                )
                # TODO: This looks weird.
                commandlist.append(" ".join(command))
            return commandlist
        else:
            final = (
                ["restic", "-r", f'"{str(Path(target_repo.path))}"']
                + prefix
                + ["backup", f'"{str(Path(task.path))}"']
                + suffix
            )

            return [" ".join(final)]

    def _build_copy_task(self, task: ResrunCopyTaskConfig):
        prefix = self._get_global_prefixes()
        suffix = []

        source_repo = self._get_repo_or_default(task.repo)
        target_repo = self.repos.get(task.copy_to)

        if not source_repo or not target_repo:
            raise ValueError("Trying to copy from/to an unknown repo!")

        # copying specific snapshots ignores every other param
        if task.snapshots:
            suffix.append(" ".join(task.snapshots))
        else:
            if task.path:
                suffix.append(f'--path "{task.path}"')
            if task.host:
                suffix.append(f'--host "{task.host}"')

        final = (
            ["restic", "-r", f'"{str(Path(target_repo.path))}"']
            + prefix
            + ["copy", "--from-repo", f'"{str(Path(source_repo.path))}"']
            + suffix
        )

        return " ".join(final)

    def _build_forget_task(self, task: ResrunForgetTaskConfig):
        prefix = self._get_global_prefixes()
        suffix = []
        target_repo = self._get_repo_or_default(task.repo)

        # FIXME: This looks just as ugly as "str if blah else None"
        #   The fuck do I do?
        keeps = [
            self._string_or_null("--keep-last ", task.keep_last),
            self._string_or_null("--keep-hourly ", task.keep_hourly),
            self._string_or_null("--keep-daily ", task.keep_daily),
            self._string_or_null("--keep-weekly ", task.keep_weekly),
            self._string_or_null("--keep-monthly ", task.keep_monthly),
            self._string_or_null("--keep-yearly ", task.keep_yearly),
        ]

        final = (
            ["restic", "-r", f'"{str(Path(target_repo.path))}"']
            + prefix
            + ["forget"]
            + keeps
            + suffix
        )

        return " ".join(filter(None, final))

    def _build_manual_task(self, task: ResrunManualTaskConfig):
        return f"restic {task.command}"
