# coding=utf-8
from flask import jsonify, current_app

from nmp_broker.api_v3 import api_v3_app
from nmp_broker.common import weixin

REQUEST_POST_TIME_OUT = 20


@api_v3_app.route('/alert/apps/weixin/access_token/get', methods=['GET'])
def get_weixin_access_token():
    auth = weixin.Auth(current_app.config['BROKER_CONFIG']['weixin_app'])
    result = auth.get_access_token_from_server()
    current_app.logger.info(result)
    return jsonify(result)
