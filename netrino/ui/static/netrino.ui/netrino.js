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
