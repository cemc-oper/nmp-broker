import requests
from flask import current_app

from nmp_broker.common.data_store.redis.alert import (
    save_weixin_access_token_to_cache,
    get_weixin_access_token_from_cache,
)

REQUEST_POST_TIME_OUT = 20


class Auth(object):
    def __init__(self, config: dict):
        """
        :param config:
            {
                "name": "WeixinAppConfig",
                "type": "record",
                "fields": [
                    {
                        name: "token",
                        type: dict,
                        fields: {
                            {"name": "corp_id", type: "string"},
                            {"name": "url", type: "string"},
                        }
                    }
                    {
                        name: "apps",
                        type: dict,
                        fields: [
                            {"name": "name", type: "string"},
                            {"name": "type", type: "string"},
                            {"name": "agentid", type: "string"},
                            {"name": "corp_secret", type: "string"},
                        ]
                    }
                ]
            }
        :return:
        """
        self.corp_id = config['token']['corp_id']
        self.url = config['token']['url']
        self.apps = config['apps']

    def get_access_token_from_server(self) -> list:
        token_results = []
        for weixin_app in self.apps:
            name = weixin_app["name"]
            corp_secret = weixin_app["corp_secret"]
            headers = {"content-type": "application/json"}
            url = self.url.format(
                corp_id=self.corp_id, corp_secret=corp_secret
            )

            token_response = requests.get(
                url,
                verify=False,
                headers=headers,
                timeout=REQUEST_POST_TIME_OUT
            )

            response_json = token_response.json()
            current_app.logger.info(response_json)
            if response_json['errcode'] == 0:
                access_token = response_json['access_token']
                save_weixin_access_token_to_cache(name, access_token)
                result = {
                    'name': name,
                    'status': 'ok',
                    'access_token': access_token
                }
            else:
                result = {
                    'name': name,
                    'status': 'error',
                    'errcode': response_json['errcode'],
                    'errmsg': response_json['errmsg']
                }
            token_results.append(result)

        return token_results

    @classmethod
    def get_access_token_from_cache(cls, app_name: str) -> str:
        return get_weixin_access_token_from_cache(app_name)

    @classmethod
    def save_access_token_to_cache(cls, app_name: str, access_token: str) -> None:
        return save_weixin_access_token_to_cache(app_name, access_token)

    def get_access_token(self) -> dict:
        tokens = dict()
        for weixin_app in self.apps:
            name = weixin_app['name']
            weixin_access_token = get_weixin_access_token_from_cache(name)
            if weixin_access_token is None:
                self.get_access_token_from_server()
                weixin_access_token = get_weixin_access_token_from_cache(name)
            tokens[name] = weixin_access_token
        return tokens
