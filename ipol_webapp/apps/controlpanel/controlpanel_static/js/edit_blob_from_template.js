
var original_set = document.getElementById("set").value;
var original_pos = document.getElementById("pos").value;
var file = document.getElementById("file");


function fileName(){
    file = document.getElementById("vr");
    if ('files' in file) {
        txt = file.files[0].name;
        document.getElementById("vr_name").innerHTML = txt;
    }
}

function removeFile(){
    file = null;
    document.getElementById("vr_name").innerHTML = "File...";
}

function deleteBlob(url, name){
    var values = {
        'name': name,
        'set': original_set,
        'pos': original_pos
    }
    $.post(url, values, 'json');
    demo_url = "/cp/blob_template/" + name;
    window.location.href = demo_url;
}

function deleteVR(url, blob_id){
    var delvr = confirm('Deleting visual representation will afect other demos and templates.\nAre you sure you want to continue?');
    if (delvr == true) {
        $.post(url, {'blob_id':blob_id}, 'json');
        window.location.reload();
    }
}