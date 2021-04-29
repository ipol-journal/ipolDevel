
function deleteBlob(url,template_id,set,pos){
    var values = {'template_id': template_id,'set': set,'pos': pos};
    $.post(url, values, 'json')
        .always(() => { window.location.reload() });
}

function deleteTemplate(url, template_id){
    var delvr = confirm('Deleting template will afect other demos.\nAre you sure you want to continue?');
    if (delvr == true) {
       var values = {
            'template_id': template_id,
        }
        $.post(url, values, 'json').then(() => {window.location.href = '/cp/templates_list/'});
    }
}

function removeDemoFromTemplate(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json');
    window.location.reload();
}