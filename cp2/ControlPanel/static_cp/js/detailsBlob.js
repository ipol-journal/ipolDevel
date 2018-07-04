var csrftoken = getCookie('csrftoken');
var VRImage;
var completeURL = document.location.href;
var decoded = decodeURI(completeURL);
var title = getParameterByName('title');
var set = getParameterByName('set');
var pos = getParameterByName('pos');
var credit = getParameterByName('credit');
var tags = getParameterByName('tags');
var thumbnail_vr = getParameterByName('vr');
var templateSelection = getParameterByName('template');
var blob = getParameterByName('thumbnail');
var blob_id = getParameterByName('id');
var realBlob = getParameterByName('blob');

document.getElementById("setName").textContent = set;
document.getElementById("Title").value = title;
document.getElementById("SET").value = set;
document.getElementById("PositionSet").value = pos;
document.getElementById("Credit").value = credit;
document.getElementById("Tags").value = tags;
document.getElementById("thumbnail_vr").src = thumbnail_vr;
document.getElementById("thumbnail").src = blob;

var show_blob = document.getElementById("download_blob");
var show_vr = document.getElementById('download_vr');
showBlob.setAttribute("href", realBlob);

//finir avec blob, car la on affiche le thumbnail
//si thumbnail alors afficher sinon dl le blob
function showVR (data){
    if (data === "undefined") {
        return 0
    }
    else {
        show_vr.setAttribute("href", lele)
    }
}

showVR(thumbnail_vr);


var form = document.getElementById('editBlobForm');
form.onsubmit = function (e) {
    e.preventDefault();
    var formData = new FormData();
    formData.append('old_set', set)
    formData.append('old_pos', pos)
    formData.append('Title', $('#Title').val());
    formData.append('SET' , $('#SET').val());
    formData.append('PositionSet', $('#PositionSet').val());
    formData.append('Credit', $('#Credit').val());
    formData.append('Tags', $('#Tags').val());
    formData.append('TemplateSelection', templateSelection);
    if (VRImage) {
        formData.append('VR', VRImage, VRImage.name);
    }
    formData.append('csrfmiddlewaretoken', csrftoken);
    $.ajax({
        url: 'detailsBlob/ajax',
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        type: 'POST',
        dataType : 'json',
        success: function(data) {
            if (data.status === 'OK') {
                alert("Redirection Templates List...")
                document.location.href = "/cp2/showTemplates?template="+templateSelection
            } else {
                alert("Error to add this Blob to the Template")
            }
        },
    })
};

$(function() {
    $("#removeVr").click(function() {
        $.ajax({
            beforeSend: function(xhr, settings) {
                delvr = confirm('Deleting visual representation will afect other demos and templates.\nAre you sure you want to continue?');
                return delvr
            },
            data : ({
                blob_id : blob_id,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            dataType: 'json',
            url: 'detailsBlob/ajax_remove_vr',
            success: function(data) {
                alert(data.status);
                document.location.reload();
            },
        });
        return false;
    });
});