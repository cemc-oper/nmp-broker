# coding: utf-8
from nwpc_workflow_model.node_status import NodeStatus


def mock_has_error_task(owner, repo):
    return {
        "error_task_list": [
            {
                "children":  [],
                "name":  "initial",
                "node_path":  "/grapes_meso_3km_post/00/initial",
                "node_type":  "task",
                "path":  "/grapes_meso_3km_post/00/initial",
                "status":  "aborted"
            }
        ],
        "timestamp":  "2018-09-26T02:37:38"
    }


def test_case_previous_is_not_aborted(app, monkeypatch):
    with app.app_context():
        from nmp_broker.common.data_store.redis import workflow
        from nmp_broker.common.workflow.status_strategy import is_new_abort_task_found
        owner = 'nwp_xp'
        repo = 'nwpc_op'
        previous_server_status = NodeStatus.queued
        error_task_dict_list = [
            {
                "children": [],
                "name": "initial",
                "node_path": "/grapes_meso_3km_post/00/initial",
                "node_type": "task",
                "path": "/grapes_meso_3km_post/00/initial",
                "status": "aborted"
            }
        ]

        monkeypatch.setattr(workflow, 'get_error_task_list_from_cache', mock_has_error_task)

        assert is_new_abort_task_found(owner, repo, previous_server_status, error_task_dict_list)


def test_case_new_found(app, monkeypatch):
    with app.app_context():
        from nmp_broker.common.data_store.redis import workflow
        from nmp_broker.common.workflow.status_strategy import is_new_abort_task_found
        owner = 'nwp_xp'
        repo = 'nwpc_op'
        previous_server_status = NodeStatus.aborted
        error_task_dict_list = [
            {
                "children": [],
                "name": "initial",
                "node_path": "/grapes_meso_3km_post/00/initial",
                "node_type": "task",
                "path": "/grapes_meso_3km_post/00/initial",
                "status": "aborted"
            },
            {
                "children": [],
                "name": "pre_data",
                "node_path": "/grapes_meso_3km_post/00/pre_data",
                "node_type": "task",
                "path": "/grapes_meso_3km_post/00/pre_data",
                "status": "aborted"
            }
        ]

        monkeypatch.setattr(workflow, 'get_error_task_list_from_cache', mock_has_error_task)

        assert is_new_abort_task_found(owner, repo, previous_server_status, error_task_dict_list)


def test_case_not_new_found(app, monkeypatch):
    with app.app_context():
        from nmp_broker.common.data_store.redis import workflow
        from nmp_broker.common.workflow.status_strategy import is_new_abort_task_found
        owner = 'nwp_xp'
        repo = 'nwpc_op'
        previous_server_status = NodeStatus.aborted
        error_task_dict_list = [
            {
                "children": [],
                "name": "initial",
                "node_path": "/grapes_meso_3km_post/00/initial",
                "node_type": "task",
                "path": "/grapes_meso_3km_post/00/initial",
                "status": "aborted"
            }
        ]

        monkeypatch.setattr(workflow, 'get_error_task_list_from_cache', mock_has_error_task)

        assert not is_new_abort_task_found(owner, repo, previous_server_status, error_task_dict_list)
