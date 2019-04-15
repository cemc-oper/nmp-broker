# coding: utf-8
from nwpc_workflow_model.node_status import NodeStatus


def test_case_previous_is_not_aborted():
    from nmp_broker.common.workflow.status_strategy import is_new_abort_root_found
    owner = 'nwp_xp'
    repo = 'nwpc_op'
    previous_server_status = NodeStatus.queued
    current_server_status = NodeStatus.aborted

    assert is_new_abort_root_found(owner, repo, previous_server_status, current_server_status)


def test_case_previous_is_aborted():
    from nmp_broker.common.workflow.status_strategy import is_new_abort_root_found
    owner = 'nwp_xp'
    repo = 'nwpc_op'
    previous_server_status = NodeStatus.aborted
    current_server_status = NodeStatus.aborted

    assert not is_new_abort_root_found(owner, repo, previous_server_status, current_server_status)
