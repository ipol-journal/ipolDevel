function deleteTemplate(url, template_id){
    var delvr = confirm('Deleting the template could afect some demos.\nAre you sure you want to continue?');
    if (delvr) {
       var values = {
            'template_id': template_id,
        }
        $.post(url, values, 'json')
            .always(() => { window.location.reload() });
    }
}

function createTemplate(url){
   var name = document.getElementById("template_name").value;
   var values = {
        'name': name,
    }
    $.post(url, values, 'json')
        .always(() => { window.location.reload() });
}

