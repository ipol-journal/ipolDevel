function fileName(){
    file = document.getElementById("file");
    if ('files' in file) {
        txt = file.files[0].name;
        document.getElementById("filename").innerHTML = txt;
    }
}

function removeFile(){
    file = null;
    document.getElementById("filename").innerHTML = "File...";
}

function blobUploaded(){
    var thumbnail = document.getElementById("thumbnail");
    var blob = document.getElementById("blob");
    var fr = new FileReader();
    fr.onload = function(e) { thumbnail.src = this.result; };
    fr.readAsDataURL(blob.files[0]);
    if (blob.files.length > 0) {
        document.getElementById("blob_name").innerHTML = blob.files[0].name;
    }
}

function removeUploadedBlob(){
    var thumbnail = document.getElementById("thumbnail");
    var blob = document.getElementById("blob");
    thumbnail.src = "";
    blob.value=null;
    document.getElementById("blob_name").innerHTML = "File...";
}

function vrUploaded(){
    var thumbnail = document.getElementById("thumbnail_vr");
    var vr = document.getElementById("vr");
    var fr = new FileReader();
    fr.onload = function(e) { thumbnail_vr.src = this.result; };
    fr.readAsDataURL(vr.files[0]);
    if (vr.files.length > 0) {
        document.getElementById("vr_name").innerHTML = vr.files[0].name;
    }
}

function removeUploadedVr(){
    var thumbnail = document.getElementById("thumbnail_vr");
    var vr = document.getElementById("vr");
    thumbnail.src = ""
    vr.value=null;
    document.getElementById("vr_name").innerHTML = "File...";
}

function blobClick(){
    var button = document.getElementById("blob");
    button.click();
}

function vrClick(){
    var button = document.getElementById("vr");
    button.click();
}

