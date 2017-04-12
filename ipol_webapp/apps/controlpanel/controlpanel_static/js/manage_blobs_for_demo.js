function deleteBlob(url,id,set,pos){
    var values = {'demo_id': id,'set': set,'pos': pos};
    $.post(url, values, 'json');
    window.location.reload(true);
}

function removeTemplateFromDemo(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json');
    window.location.reload(true);
}
function addTemplateToDemo(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json');
    window.location.reload(true);
}


