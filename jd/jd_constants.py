# -*- coding: utf-8 -*-
# !/usr/bin/python

class JdConstants:
    """
    JD API constant definition
    """
    API_DOMAIN = 'https://api.m.jd.com'
    API_URL = '{}/api'.format(API_DOMAIN)
    CLIENT_ACTION_URL = '{}/client.action'.format(API_DOMAIN)
    USER_ROUTING = 'https://divide.jd.com/user_routing?skuId={skuId}&from=app'
    TAK_URL = 'https://tak.jd.com/t/871A9?_t={timestamp}'
    ORDER_SERVICE_URL = 'https://marathon.jd.com/seckillnew/orderService/init.action'

    """
    JD FunctionId constant definition
    """
    GEN_TOKEN_FUNC = 'genToken'
    APPOINT_FUNC = 'appoint'
    IS_APPOINT_FUNC = 'isAppoint'
