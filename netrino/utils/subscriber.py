from luxon import g
from luxon import js

def sub_from_tenant(tenant_id, region):
    url = '/v1/subscribers'
    api = g.current_request.context.api

    api.collect_endpoints(region,
                          g.current_request.context_interface)

    subscriber = api.execute('GET',
                             url,
                             endpoint='subscriber').json

    return subscriber['payload'][0]['id']

def sub_from_order(order_id, region):
    url = '/v1/order/' + order_id
    api = g.current_request.context.api

    api.collect_endpoints(region,
                          g.current_request.context_interface)

    order = api.execute('GET',
                             url,
                             endpoint='orchestration').json

    return js.loads(order['metadata'])['subscriber']
