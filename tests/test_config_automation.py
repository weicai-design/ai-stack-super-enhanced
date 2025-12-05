import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config_automation import (  # noqa: E402
    EnvironmentConfigManager,
    DeploymentAutomation,
)


def _ensure_writeable(path: Path):
    try:
        path.write_text("probe", encoding="utf-8")
        path.unlink(missing_ok=True)
    except PermissionError:
        pytest.skip("沙箱禁止写入当前路径，跳过配置自动化测试。")


@pytest.fixture()
def sample_profiles(writable_tmp_path: Path):
    profiles_dir = writable_tmp_path / "profiles"
    profiles_dir.mkdir()
    profile_file = profiles_dir / "dev.yaml"
    profile_file.write_text(
        """
name: dev
description: test
env:
  APP_ENV: dev
""",
        encoding="utf-8",
    )
    return profiles_dir


def test_apply_profile_writes_env(writable_tmp_path: Path, sample_profiles: Path):
    tmp_path = writable_tmp_path
    out_path = tmp_path / ".env.runtime"
    _ensure_writeable(out_path)
    manager = EnvironmentConfigManager(
        profiles_dir=sample_profiles,
        output_env_path=out_path,
        history_path=tmp_path / "history.jsonl",
    )
    result = manager.apply_profile("dev", overrides={"ADDITIONAL": "1"})
    assert out_path.exists()
    env_text = out_path.read_text(encoding="utf-8")
    assert "APP_ENV=dev" in env_text
    assert "ADDITIONAL=1" in env_text
    assert result["profile"]["name"] == "dev"
    history = manager.get_history(limit=1)
    assert history and history[0]["profile"] == "dev"


@pytest.mark.asyncio
async def test_deployment_pipeline_dry_run(writable_tmp_path: Path, sample_profiles: Path):
    tmp_path = writable_tmp_path
    pipeline_file = tmp_path / "pipeline.yaml"
    out_env = tmp_path / ".env.runtime"
    _ensure_writeable(out_env)
    pipeline_file.write_text(
        """
steps:
  - name: dummy
    command: "echo hello"
""",
        encoding="utf-8",
    )
    manager = EnvironmentConfigManager(
        profiles_dir=sample_profiles,
        output_env_path=out_env,
        history_path=tmp_path / "history.jsonl",
    )
    deployment = DeploymentAutomation(
        pipeline_path=pipeline_file,
        history_dir=tmp_path / "history",
        config_manager=manager,
    )
    summary = await deployment.run_pipeline("dev", dry_run=True)
    assert summary["dry_run"] is True
    assert summary["steps"][0]["status"] == "skipped"
    history_file = deployment.history_file
    assert history_file.exists()
    records = history_file.read_text(encoding="utf-8").strip().splitlines()
    assert records and json.loads(records[-1])["dry_run"] is True

