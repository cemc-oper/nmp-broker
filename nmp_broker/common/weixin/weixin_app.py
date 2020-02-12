from collections import defaultdict
from datetime import datetime

import requests
from flask import current_app, json

from nmp_broker.common.weixin.auth import Auth, REQUEST_POST_TIME_OUT


class WeixinApp(object):
    def __init__(self, weixin_config: dict, cloud_config: dict):
        self.weixin_config = weixin_config
        self.cloud_config = cloud_config
        self.auth = Auth(self.weixin_config)

    def send_warning_message(self, weixin_app: dict, warning_data: dict):
        """
        :param weixin_app: config for weixin app
        :param warning_data:
            {
                "name": "WarningData",
                "namespace": "WeixinApp",
                "type": "record",
                "fields": [
                    {"name": "owner", type: "string"},
                    {"name": "repo", type: "string"},
                    {"name": "server_name", type: "string"},
                    {"name": "message_datetime", type: "datetime"},
                    {"name": "suite_error_map", type: "array"},
                    {"name": "aborted_tasks_blob_id", type: "int"},
                ]
            }
        :return:
        """
        # TODO: change server_name
        app_name = weixin_app["name"]
        owner = warning_data['owner']
        repo = warning_data['repo']
        current_app.logger.info('[{owner}/{repo}] get error task. Pushing warning message to weixin...'.format(
            owner=owner, repo=repo
        ))

        if warning_data['aborted_tasks_blob_id']:
            message_url = (self.cloud_config['base']['url'] + '/{owner}/{repo}/aborted_tasks/{id}').format(
                owner=warning_data['owner'],
                repo=warning_data['repo'],
                id=warning_data['aborted_tasks_blob_id']
            )
        else:
            message_url = self.cloud_config['base']['url']

        form_suite_error_list = []
        for a_suite_name in warning_data['suite_error_map']:
            a_suite_item = warning_data['suite_error_map'][a_suite_name]
            if len(a_suite_item['error_task_list']) > 0:
                form_suite_error_list.append({
                    'name': a_suite_item['name'],
                    'count': len(a_suite_item['error_task_list'])
                })

        task_list = '出错系统列表：'
        for a_suite in form_suite_error_list:
            task_list += "\n" + a_suite['name'] + ' : ' + str(a_suite['count'])

        articles = [
            {
                "title": "业务系统：{server_name}运行出错".format(server_name=warning_data['server_name']),
                "picurl": "http://wx2.sinaimg.cn/large/4afdac38ly1feu4tqm9c6j21kw0sggmu.jpg",
                "url": message_url
            },
            {
                "title": "项目：{owner}/{repo}".format(
                    owner=warning_data['owner'],
                    repo=warning_data['repo']
                ),
                "url": message_url
            },
            {
                "title":
                    "日期 : {error_date}\n".format(
                        error_date=datetime.utcnow().strftime("%Y-%m-%d"))
                    + "时间 : {error_time}".format(
                        error_time=datetime.utcnow().strftime("%H:%M:%S")),
                "url": message_url
            },
            {
                "title": task_list,
                "url": message_url
            },
            {
                "title": '点击查看详情',
                "url": message_url
            }
        ]

        warning_post_message = {
            "agentid": 2,
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }

        target = weixin_app['target']
        warning_post_message.update(target)

        self._send_message(app_name, warning_post_message)

    def send_sms_node_task_warn(self, weixin_app: dict, message: dict):
        app_name = weixin_app["name"]

        node_list_content = ''
        for a_unfit_node in message['data']['unfit_nodes']:

            node_list_content += a_unfit_node['node_path'] + ':'
            unfit_map = defaultdict(int)
            for a_check_condition in a_unfit_node['unfit_check_list']:
                unfit_map[a_check_condition['type']] += 1

            for (type_name, count) in unfit_map.items():
                node_list_content += " {type_name}[{count}]".format(
                    type_name=type_name, count=count)
            node_list_content += '\n'

        message_url = (self.cloud_config['base']['url'] + '/{owner}/{repo}/task_check/unfit_nodes/{id}').format(
            owner=message['data']['owner'],
            repo=message['data']['repo'],
            id=message['data']['unfit_nodes_blob_id']
        )

        articles = [
            {
                'title': "业务系统异常：{repo} 节点状态".format(repo=message['data']['repo']),
                "picurl": "http://wx2.sinaimg.cn/mw690/4afdac38ly1feqnwb44kkj2223112wfj.jpg",
                'url': message_url
            },
            {
                "title": "{owner}/{repo}".format(
                    owner=message['data']['owner'],
                    repo=message['data']['repo']
                ),
                "description": message['data']['task_name'],
                'url': message_url
            },
            {
                'title':
                    "日期 : {error_date}\n".format(
                        error_date=datetime.utcnow().strftime("%Y-%m-%d"))
                    + "时间 : {error_time}".format(
                        error_time=datetime.utcnow().strftime("%H:%M:%S")),
                'url': message_url
            },
            {
                "title": message['data']['task_name'] + " 运行异常",
                'url': message_url
            },
            {
                'title': '异常任务列表\n' + node_list_content,
                'description': '点击查看详情',
                'url': message_url
            }
        ]

        warning_post_message = {
            "agentid": 2,
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }
        target = weixin_app['target']
        warning_post_message.update(target)

        self._send_message(app_name, warning_post_message)

    def send_sms_node_task_message(self, weixin_app: dict, message_data):
        app_name = weixin_app["name"]

        message_url = (self.cloud_config['base']['url'] + '/{owner}/{repo}/task_check/unfit_nodes/{id}').format(
            owner=message_data['owner'],
            repo=message_data['repo']
        )
        articles = [
            {
                "title": "业务系统：SMS节点状态检查",
                "picurl": "http://wx2.sinaimg.cn/large/4afdac38ly1feqnewxygsj20hs08wt8u.jpg",
                'url': message_url
            },
            {
                "title": "{owner}/{repo}".format(
                    owner=message_data['data']['owner'],
                    repo=message_data['data']['repo']
                ),
                "description": message_data['data']['task_name'],
                'url': message_url
            },
            {
                "title":
                    "{error_date} {error_time}".format(
                        error_date=datetime.utcnow().strftime("%Y-%m-%d"),
                        error_time=datetime.utcnow().strftime("%H:%M:%S")
                    ),
                'url': message_url
            },
            {
                "title": message_data['data']['task_name'] + " 运行正常",
                'url': message_url
            }
        ]

        post_message = {
            "agentid": 2,
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }
        target = weixin_app['target']
        post_message.update(target)

        self._send_message(app_name, post_message)

    def send_loadleveler_status_warning_message(
            self,
            weixin_app: dict,
            user,
            plugin_check_result,
            abnormal_jobs_blob_id):
        app_name = weixin_app["name"]
        text = ""
        for a_owner in plugin_check_result['data']['categorized_result']:
            text += "\n{owner}:{number}".format(
                owner=a_owner,
                number=plugin_check_result['data']['categorized_result'][a_owner])
        message_url = (self.cloud_config['base']['url'] + '/hpc/{user}/loadleveler/abnormal_jobs/{abnormal_jobs_blob_id}').format(
            user=user,
            abnormal_jobs_blob_id=abnormal_jobs_blob_id
        )
        articles = [
            {
                "title": "业务系统：队列异常",
                "picurl": "http://wx2.sinaimg.cn/large/4afdac38ly1fg4b31u8dqj21kw0sgjto.jpg",
                "url": message_url
            },
            {
                "title":
                    "{error_date} {error_time}".format(
                        error_date=datetime.utcnow().strftime("%Y-%m-%d"),
                        error_time=datetime.utcnow().strftime("%H:%M:%S")
                    ),
                "url": message_url
            },
            {
                "title": "异常用户:" + text,
                "url": message_url
            }

        ]
        post_message = {
            "agentid": 2,
            "msgtype": "news",
            "news": {
                "articles": articles
            }
        }

        target = weixin_app['target']
        post_message.update(target)

        self._send_message(app_name, post_message)

    def _send_message(self, app_name: str, message: dict):
        auth = Auth(self.weixin_config)
        tokens = auth.get_access_token()

        post_url = self.weixin_config['warn']['url'].format(
            weixin_access_token=tokens[app_name]
        )
        post_headers = {
            'content-type': 'application/json'
        }
        post_data = json.dumps(message, ensure_ascii=False).encode('utf8')

        result = requests.post(
            post_url,
            data=post_data,
            verify=False,
            headers=post_headers,
            timeout=REQUEST_POST_TIME_OUT
        )
        current_app.logger.info(result.json())