function deleteBlob(url,id,set,pos){
    var values = {'demo_id': id,'set': set,'pos': pos};
    $.post(url, values, 'json')
        .always(() => window.location.reload());
}

function removeTemplateFromDemo(url,id,template_id){
    var values = {'demo_id': id,'template_id': template_id};
    $.post(url, values, 'json')
        .always(() => window.location.reload());
}
function addTemplateToDemo(url,id,template_id){
    var values = {'demo_id': id,'template_id': template_id};
    $.post(url, values, 'json')
        .always(() => window.location.reload());
}
