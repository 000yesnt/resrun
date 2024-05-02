import pytest
import os


def sepconv(p: str) -> str:
    return p.replace("/", os.sep)


@pytest.mark.xfail
def test_premature_build(builder):
    builder.build()


@pytest.mark.parametrize(
    "config",
    [
        pytest.param({"repos": [], "tasks": []}, id="empty_repos_tasks"),
        pytest.param(
            {"repos": [{"path": "path1", "id": "path1", "default": True}], "tasks": []},
            id="empty_tasks",
        ),
        pytest.param({"repos": [], "tasks": [{"path": "path1"}]}, id="empty_repos"),
        pytest.param(
            {
                "repos": [
                    {"path": "path1", "id": "path1", "default": True},
                    {"path": "path2", "id": "path2", "default": True},
                ],
                "tasks": [{"path": "path1"}],
            },
            id="conflicting_defaults",
        ),
    ],
)
def test_bad_config(config, builder):
    """Test invalid configs."""
    try:
        builder.load_config(config)
        pytest.xfail("No error thrown!")
    except Exception as e:
        assert type(e) is ValueError


@pytest.mark.parametrize(
    "config,expected",
    [
        pytest.param(
            {"tasks": [{"path": "/home/test/path1"}]},
            [sepconv('restic -r "/home/test/repo1" -v backup "/home/test/path1"')],
            id="single_path",
        ),
        pytest.param(
            {"tasks": [{"path": "/home/test/path1", "repo": "repo2"}]},
            [sepconv('restic -r "/home/test/repo2" -v backup "/home/test/path1"')],
            id="single_path_repo2",
        ),
        pytest.param(
            {
                "tasks": [
                    {
                        "path": [
                            "/home/test/path1",
                            "/home/test/path2",
                            "/home/test/path3",
                        ]
                    }
                ]
            },
            [
                sepconv('restic -r "/home/test/repo1" -v backup "/home/test/path1"'),
                sepconv('restic -r "/home/test/repo1" -v backup "/home/test/path2"'),
                sepconv('restic -r "/home/test/repo1" -v backup "/home/test/path3"'),
            ],
            id="multiple_path",
        ),
        pytest.param(
            {
                "tasks": [
                    {
                        "path": "/home/test/path1",
                        "exclude_file": "/home/test/exclude_override",
                    }
                ],
                "repos": [
                    {
                        "id": "excludefile",
                        "path": "/home/test/repo1",
                        "exclude_file": "/home/test/exclude",
                        "default": True,
                    }
                ],
            },
            [
                sepconv(
                    'restic -r "/home/test/repo1" -v backup "/home/test/path1" '
                    '--exclude-file="/home/test/exclude_override"'
                )
            ],
            id="exclude_file_override",
        ),
    ],
)
def test_backup(base_config, config, expected, builder):
    """Test different functions of the backup task type."""
    builder.load_config(base_config | config)
    assert builder.build() == expected


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            {
                "repos": [{"path": "/home/test/repo1", "id": "repo1"}],
                "tasks": [
                    {"path": "/home/test/path1", "repo": "repo_that_doesnt_exist"}
                ],
            },
            id="bad_repo_id",
        )
    ],
)
@pytest.mark.xfail
def test_bad_backup(base_config, config, builder):
    """Test bad backup configurations"""
    builder.load_config(base_config | config)
    builder.build()


@pytest.mark.parametrize(
    "config,expected",
    [
        pytest.param(
            {"tasks": [{"task": "copy", "copy_to": "repo2"}]},
            [
                sepconv(
                    'restic -r "/home/test/repo2" -v copy --from-repo "/home/test/repo1"'
                )
            ],
            id="copy_default_to_repo2",
        ),
        pytest.param(
            {"tasks": [{"task": "copy", "repo": "repo2", "copy_to": "repo1"}]},
            [
                sepconv(
                    'restic -r "/home/test/repo1" -v copy --from-repo "/home/test/repo2"'
                )
            ],
            id="copy_repo2_to_repo1",
        ),
        pytest.param(
            {
                "tasks": [
                    {
                        "task": "copy",
                        "copy_to": "repo2",
                        "snapshots": ["410b18a2", "4e5d5487", "latest"],
                        "path": "/home/test/path1",
                        "host": "computer",
                    }
                ]
            },
            [
                sepconv(
                    'restic -r "/home/test/repo2" -v copy --from-repo "/home/test/repo1" 410b18a2 4e5d5487 latest'
                )
            ],
            id="copy_snapshots_overrides_others",
        ),
        pytest.param(
            {
                "tasks": [
                    {
                        "task": "copy",
                        "copy_to": "repo2",
                        "path": "/home/test/path1",
                        "host": "computer",
                    }
                ]
            },
            [
                sepconv(
                    'restic -r "/home/test/repo2" -v copy --from-repo "/home/test/repo1" --path "/home/test/path1" --host "computer"'
                )
            ],
            id="copy_path_host",
        ),
    ],
)
def test_copy(base_config, config, expected, builder):
    """Test different functions of the copy task type."""
    builder.load_config(base_config | config)
    assert builder.build() == expected


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            {
                "repos": [{"path": "/home/test/repo1", "id": "repo1"}],
                "tasks": [
                    {
                        "task": "copy",
                        "repo": "repo_that_doesnt_exist",
                        "copy_to": "repo1",
                    }
                ],
            },
            id="bad_source_repo",
        ),
        pytest.param(
            {
                "repos": [{"path": "/home/test/repo1", "id": "repo1"}],
                "tasks": [
                    {
                        "task": "copy",
                        "repo": "repo1",
                        "copy_to": "repo_that_doesnt_exist",
                    }
                ],
            },
            id="bad_target_repo",
        ),
        pytest.param(
            {
                "repos": [{"path": "/home/test/repo1", "id": "repo1"}],
                "tasks": [{"task": "copy", "repo": "repo1", "copy_to": "repo1"}],
            },
            id="copying_to_self",
        ),
    ],
)
@pytest.mark.xfail
def test_bad_copy(base_config, config, builder):
    """Test bad copy configurations"""
    builder.load_config(base_config | config)
    builder.build()


@pytest.mark.parametrize(
    "config,expected",
    [
        pytest.param(
            {
                "tasks": [
                    {
                        "task": "forget",
                        "keep_last": 1,
                        "keep_hourly": 2,
                        "keep_daily": 3,
                        "keep_weekly": 4,
                        "keep_monthly": 5,
                        "keep_yearly": 6,
                    }
                ]
            },
            [
                sepconv(
                    'restic -r "/home/test/repo1" -v forget --keep-last 1 --keep-hourly 2 --keep-daily 3 '
                    "--keep-weekly 4 --keep-monthly 5 --keep-yearly 6"
                )
            ],
            id="forget_all_args",
        ),
        pytest.param(
            {"tasks": [{"task": "forget", "keep_last": 1}]},
            [sepconv('restic -r "/home/test/repo1" -v forget --keep-last 1')],
            id="forget_keep_last",
        ),
    ],
)
def test_forget(base_config, config, expected, builder):
    """Test different functions of the forget task type."""
    builder.load_config(base_config | config)
    assert builder.build() == expected


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            {
                "repos": [{"path": "/home/test/repo1", "id": "repo1"}],
                "tasks": [{"task": "forget", "repo": "repo_that_doesnt_exist"}],
            },
            id="bad_repo",
        )
    ],
)
@pytest.mark.xfail
def test_bad_forget(base_config, config, builder):
    """Test bad forget configurations"""
    builder.load_config(base_config | config)
    builder.build()


def test_manual(base_config, builder):
    config = {"tasks": [{"task": "manual", "command": "test"}]}
    builder.load_config(base_config | config)
    assert builder.build() == ["restic test"]
