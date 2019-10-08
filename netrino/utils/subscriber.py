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


def sub_from_order(order_id, metadata, api=None):
    if api is None:
        api = g.current_request.context.api

    region = metadata['region']
    package_id = metadata['package']

    url = '/v1/order/' + order_id

    api.collect_endpoints(region,
                          g.current_request.context_interface)

    order = api.execute('GET',
                        url,
                        endpoint='orchestration').json

    order_metadata = js.loads(order['metadata'])

    subscriber = order_metadata['subscriber']

    pkg = api.execute('GET',
                      'v1/package/' + package_id,
                      endpoint='subscriber').json

    return subscriber, pkg
