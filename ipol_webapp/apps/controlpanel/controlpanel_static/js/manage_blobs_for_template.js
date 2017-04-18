
function deleteBlob(url,name,set,pos){
    var values = {'name': name,'set': set,'pos': pos};
    $.post(url, values, 'json');
    window.location.reload(true);
}

function deleteTemplate(url, name){
    var delvr = confirm('Deleting template will afect other demos.\nAre you sure you want to continue?');
    if (delvr == true) {
       var values = {
            'name': name,
        }
        $.post(url, values, 'json');
        window.location.href = '/cp/templates_list/'
    }
}

function removeDemoFromTemplate(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json');
    window.location.reload(true);
}