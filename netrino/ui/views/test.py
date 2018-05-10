
from luxon import register_resource
from luxon import g
from luxon import render_template

g.nav_menu.add('/Infrastructure/Netrino/Test', '/infrastructure/netrino/test',
               'admin')


@register_resource(['GET', 'POST'] , '/infrastructure/netrino/test', 'admin')
def test(req, resp):
    form = req.form_json
    response = g.client.execute('GET', '/v1/test', endpoint='netrino')
    test = response.json
    if req.method == 'POST':
        response = g.client.execute('POST', '/v1/test', data=form, endpoint='netrino')
        form_reply = response.body
    else:
        form_reply = "none"
    return render_template('netrino.ui/test.html', api_reply=test['test'],
                           form=form, form_reply=form_reply)


