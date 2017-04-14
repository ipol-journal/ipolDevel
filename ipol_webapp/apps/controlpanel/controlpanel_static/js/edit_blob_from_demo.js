
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

function deleteBlob(url, demo_id){
    var values = {
        'demo_id': demo_id,
        'set': original_set,
        'pos': original_pos
    }
    $.post(url, values, 'json');
    demo_url = "/cp/blob_demo/" + demo_id;
    window.location.href = demo_url;
}

function deleteVR(url, blob_id){
    var delvr = confirm('Deleting visual representation will afect other demos.\nAre you sure you want to continue?');
    if (delvr == true) {
        $.post(url, {'blob_id':blob_id}, 'json');
        window.location.reload();
    }
}