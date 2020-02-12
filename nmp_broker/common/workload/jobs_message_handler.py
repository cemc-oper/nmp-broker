# coding: utf-8
import datetime
import gzip

import requests
from flask import current_app, json

from nmp_model.mongodb.blobs.workload.abnormal_jobs import AbnormalJobsBlob
from nmp_model.mongodb.cache.workload_cache import JobListContent

import nmp_broker.common.weixin.weixin_app
from nmp_broker.common import data_store
from nmp_broker.plugins.loadleveler import long_time_operation_job_warn


REQUEST_POST_TIME_OUT = 20


def handle_jobs_message(owner, repo, message):
    message['data']['type'] = JobListContent.__name__
    status_cache = data_store.save_workload_status_to_cache(owner, repo, message)

    workload_system = message['data']['workload_system']

    if workload_system == "loadleveler":
        handle_loadleveler_jobs(owner, repo, message)
    else:
        current_app.logger.warn("workload system is not supported: {workload_system}".format(
            workload_system=workload_system))

    current_app.logger.info("post workload jobs to cloud...{owner}/{repo}".format(owner=owner, repo=repo))

    post_message = {
        'app': 'nmp_broker',
        'event': 'post_workload_jobs',
        'timestamp': datetime.datetime.utcnow(),
        'data': {
            'type': 'nmp_model_job_list',
            'status': status_cache.to_mongo().to_dict()
        }
    }

    post_data = {
        'message': json.dumps(post_message)
    }
    post_url = current_app.config['BROKER_CONFIG']['workload']['jobs']['cloud']['put']['url'].format(
        owner=owner,
        rpeo=repo
    )

    current_app.logger.info('gzip the data...')
    gzipped_post_data = gzip.compress(bytes(json.dumps(post_data), 'utf-8'))
    current_app.logger.info('gzip the data...done')
    response = requests.post(
        post_url,
        data=gzipped_post_data,
        headers={
            'content-encoding': 'gzip'
        },
        timeout=REQUEST_POST_TIME_OUT
    )
    current_app.logger.info("post workload jobs to cloud...done {response}".format(response=response))


def handle_loadleveler_jobs(owner, repo, message):
    warn_strategy = current_app.config['BROKER_CONFIG']['workload']['jobs']['warn']['strategy']
    plugin_result = long_time_operation_job_warn.warn_long_time_operation_job(owner, repo, message, warn_strategy)
    if plugin_result:
        # if False:
        if not plugin_result['data']['warn_flag']:
            current_app.logger.info("Found long time operation jobs. But there is no new one...Skip")
        else:
            current_app.logger.info("Found new long time operation jobs. Send warn message.")

            model_result = data_store.save_abnormal_jobs_to_nmp_model_system(
                owner, repo, plugin_result)

            abnormal_jobs_blob_id = None
            for a_blob in model_result['blobs']:
                if isinstance(a_blob, AbnormalJobsBlob):
                    abnormal_jobs_blob_id = a_blob.ticket_id
                    current_app.logger.info(abnormal_jobs_blob_id)

            post_message = {
                'app': 'nmp_broker',
                'event': 'post_workload_jobs',
                'timestamp': datetime.datetime.utcnow(),
                'data': {
                    'type': 'nmp_model',
                    'blobs': [blob.to_mongo().to_dict() for blob in model_result['blobs']],
                    'trees': [blob.to_mongo().to_dict() for blob in model_result['trees']],
                    'commits': [blob.to_mongo().to_dict() for blob in model_result['commits']],
                }
            }

            website_post_data = {
                'message': json.dumps(post_message)
            }

            current_app.logger.info('gzip the data...')
            gzipped_post_data = gzip.compress(bytes(json.dumps(website_post_data), 'utf-8'))
            current_app.logger.info('gzip the data...done')

            website_url = current_app.config['BROKER_CONFIG']['workload']['jobs']['cloud']['put']['url'].format(
                owner=owner,
                repo=repo
            )
            response = requests.post(
                website_url,
                data=gzipped_post_data,
                headers={
                    'content-encoding': 'gzip'
                },
                timeout=REQUEST_POST_TIME_OUT
            )
            current_app.logger.info("post workload alert to weixin...{response}".format(response=response))

            weixin_app = nmp_broker.common.weixin.weixin_app.WeixinApp(
                weixin_config=current_app.config['BROKER_CONFIG']['weixin_app'],
                cloud_config=current_app.config['BROKER_CONFIG']['cloud']
            )
            weixin_app.send_loadleveler_status_warning_message(
                owner, plugin_result, abnormal_jobs_blob_id)
