function deleteTemplate(url, name){
    var delvr = confirm('Deleting the template could afect some demos.\nAre you sure you want to continue?');
    if (delvr == true) {
       var values = {
            'name': name,
        }
        $.post(url, values, 'json');
        window.location.reload();
    }
}

function createTemplate(url){
   var name = document.getElementById("template_name").value;
   var values = {
        'name': name,
    }
    $.post(url, values, 'json');
    window.location.reload();
}

