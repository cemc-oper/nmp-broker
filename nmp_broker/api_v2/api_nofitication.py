# coding=utf-8
from flask import jsonify, current_app

import nmp_broker.common.weixin.auth
from nmp_broker.api_v2 import api_v2_app
from nmp_broker.common import weixin, ding_talk, data_store

REQUEST_POST_TIME_OUT = 20


@api_v2_app.route('/dingtalk/access_token/get', methods=['GET'])
def get_dingtalk_access_token():
    auth = ding_talk.Auth(current_app.config['BROKER_CONFIG']['ding_talk_app']['token'])
    result = auth.get_access_token_from_server()
    print(result)
    return jsonify(result)


@api_v2_app.route('/weixin/access_token/get', methods=['GET'])
def get_weixin_access_token():
    auth = nmp_broker.common.weixin.auth.Auth(current_app.config['BROKER_CONFIG']['weixin_app'])
    result = auth.get_access_token_from_server()
    print(result)
    return jsonify(result)


@api_v2_app.route('/ticket/new')
def get_tickets():
    ticket = data_store.get_new_64bit_ticket()
    if ticket is None:
        result = {
            'error': 'error',
            'message': "can't get a new 64bit ticket"
        }
    else:
        result ={
            'ticket': ticket
        }
    return jsonify(result)
