# coding=utf-8
import json
from collections import defaultdict
from nmp_broker.plugins.loadleveler import loadleveler_filter
from nwpc_hpc_model.workload.filter_condition import get_property_data

from nmp_broker.common.database import redis_client


def save_long_time_operation_job_list_to_cache(owner, repo, job_items):
    key = "workload/{owner}/{repo}/long_time_operation_job_warn/job_items".format(
        owner=owner, repo=repo)
    redis_client.set(key, json.dumps(job_items))


def get_long_time_operation_job_list_from_cache(owner, repo):
    key = "workload/{owner}/{repo}/long_time_operation_job_warn/job_items".format(
        owner=owner, repo=repo)
    result = redis_client.get(key)
    if result is None:
        return None
    result = result.decode()
    return json.loads(result)


def check_using_new_id_strategy(owner, repo, target_job_items):
    warn_flag = True
    cached_job_items = get_long_time_operation_job_list_from_cache(owner, repo)
    if cached_job_items:
        warn_flag = False
        target_job_ids = [get_property_data(a_job, "llq.id") for a_job in target_job_items]
        cached_job_ids = [get_property_data(a_job, "llq.id") for a_job in cached_job_items]
        for a_job_id in target_job_ids:
            if a_job_id not in cached_job_ids:
                warn_flag = True
                break
    return warn_flag


def check_using_always_strategy(owner, repo, target_job_items):
    return True


def warn_long_time_operation_job(owner, repo, message, warn_strategy):
    job_items = message['data']['response']['items']
    filter_results = loadleveler_filter.apply_filters(job_items)
    long_time_result = filter_results[0]
    target_job_items = long_time_result['target_job_items']
    if len(target_job_items) > 0:
        print("there is long time job in loadleveler")

        if warn_strategy == 'always':
            warn_flag = check_using_always_strategy(owner, repo, target_job_items)
        elif warn_strategy == 'new_job':
            warn_flag = check_using_new_id_strategy(owner, repo, target_job_items)
        else:
            raise ValueError('strategy is not supported:', warn_strategy)

        save_long_time_operation_job_list_to_cache(owner, repo, target_job_items)
        categorized_result = defaultdict(int)
        for a_job in target_job_items:
            owner = get_property_data(a_job, "llq.owner")
            categorized_result[owner] += 1
        return {
            'data': {
                'workload_system': message['data']['workload_system'],
                'collected_time': message['data']['collected_time'],
                'plugins': [
                    {
                        'name': 'warn_long_time_operation_job'
                    }
                ],
                'target_job_items': target_job_items,
                'categorized_result': categorized_result,
                'warn_flag': warn_flag,
            },
        }
    else:
        return None
