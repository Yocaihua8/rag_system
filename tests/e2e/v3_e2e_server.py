from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.server import create_app  # noqa: E402


server: uvicorn.Server | None = None


def create_e2e_app(v2_db_path: Path, v3_db_path: Path) -> FastAPI:
    test_app = create_app(
        db_path=v2_db_path,
        v3_db_path=v3_db_path,
        enable_v3=True,
    )

    @test_app.post('/__e2e__/shutdown')
    async def shutdown() -> dict[str, str]:
        if server is not None:
            server.should_exit = True
        return {'status': 'shutting_down'}

    @test_app.post('/__e2e__/approval')
    async def create_pending_approval(payload: dict[str, str]) -> dict[str, str]:
        """Create persisted approval state for the browser-only approval flow.

        This route is mounted only by the Playwright server.  It exercises the
        production v3 store transition rather than replacing the UI with a mock.
        """
        project_id = str(payload.get('project_id', '')).strip()
        store = test_app.state.v3_store
        if not project_id or store.get_project(project_id) is None:
            raise HTTPException(status_code=404, detail='project not found')

        # These synchronous store transitions complete in this request before
        # the executor event loop can claim the newly created queued run.
        task_response = store.create_task(
            project_id=project_id,
            title='E2E 审批确认',
            prompt='Verify the pending approval flow.',
            depth='standard',
            idempotency_key='e2e-approval-task',
            request_hash='e2e-approval-task-v1',
        )
        task = task_response['task']
        message = task_response['initial_message']
        run_response = store.create_run_with_steps(
            task_id=task['id'],
            input_message_id=message['id'],
            workflow_key='e2e.approval.v1',
            workflow_version=1,
            workflow_checksum='e2e-approval-v1',
            depth='standard',
            steps=[{
                'step_key': 'approval-request',
                'node_type': 'external.write',
                'effect_kind': 'external_write',
                'input': {'purpose': 'browser approval coverage'},
            }],
            idempotency_key='e2e-approval-run',
            request_hash='e2e-approval-run-v1',
        )
        run = run_response['run']
        claim = store.claim_next_run(worker_id='e2e-approval-fixture', lease_seconds=30)
        if claim is None or claim['run']['id'] != run['id']:
            raise HTTPException(status_code=409, detail='approval fixture run was not claimed')
        requested = store.request_approval(
            task_id=task['id'],
            run_id=run['id'],
            step_id=claim['step']['id'],
            action_type='github.create_issue',
            target='owner/e2e-repository',
            payload={
                'unchanged': '不会修改本地项目文件',
                'undo': '可通过关闭测试 issue 撤销',
            },
            request_hash='a' * 64,
            resource_version='e2e-v1',
            idempotency_key='e2e-approval-request',
            idempotency_request_hash='e2e-approval-request-v1',
        )
        return {
            'task_id': task['id'],
            'run_id': run['id'],
            'approval_id': requested['approval']['id'],
        }

    return test_app


if __name__ == '__main__':
    v2_db_path = Path(os.environ['KI_V3_E2E_V2_DB_PATH']).resolve()
    v3_db_path = Path(os.environ['KI_V3_E2E_DB_PATH']).resolve()
    v2_db_path.parent.mkdir(parents=True, exist_ok=True)
    v3_db_path.parent.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get('KI_V3_E2E_PORT', '18766'))
    target_app = create_e2e_app(v2_db_path, v3_db_path)
    config = uvicorn.Config(
        target_app,
        host='127.0.0.1',
        port=port,
        timeout_graceful_shutdown=5,
    )
    server = uvicorn.Server(config)
    print(f'Knowledge Island v3 E2E is running at http://127.0.0.1:{port}')
    raise SystemExit(0 if server.run() is None else 1)
