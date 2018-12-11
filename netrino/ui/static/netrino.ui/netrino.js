function reset_interface(e) {
    $('#role_add').val(null).trigger('change');
    domain = $('#role_add_domain').val();
    if (domain == '') {
        domain = 'None'
    }
    tenant_id = $('#role_add_tenant_id').val();
    $('#role_add').attr('data-url','/v1/access/' + domain + '/' + tenant_id);
}
function reset_model(e) {
    $('#role_add_tenant_id').val(null).trigger('change');
    domain = $('#role_add_domain').val()
    if (domain == '') {
        domain = 'None'
    }
    $('#role_add_tenant_id').attr('data-url','/v1/tenants/' + domain);
    reset_interface(e);
}

function addSelect2src(select_id, name, element_id, url) {
    var o = new Option(select_id, name);
    $(o).html(name);
    $(o).attr('selected',true);
    $(o).attr('value',select_id);
    $('select#'+element_id).append(o);
    $('select#'+element_id).attr('data-url',url);
    $('select#'+element_id).attr('data-endpoint','orchestration');
    $('select#'+element_id).append();
}
