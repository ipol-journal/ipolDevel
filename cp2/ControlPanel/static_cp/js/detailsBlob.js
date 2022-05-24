var csrftoken = getCookie('csrftoken');
var VRImage;
var completeURL = document.location.href;
var decoded = decodeURI(completeURL);
var demo_id = getParameterByName('demo_id');
var template_id = getParameterByName('template_id');
var template_name = getParameterByName('template_name');
var pos = getParameterByName('pos');
var set = getParameterByName('set');
var vr;
let blob_id;

$(document).ready(function(){
    let location_url = `${window.location.protocol}//${window.location.host}`;
    let blob = {};
    let fetch_url;
    let url;
    if (template_id) {
        fetch_url = `${location_url}/api/blobs/get_template_blobs?template_id=${template_id}`
    } else {
        fetch_url = `${location_url}/api/blobs/get_demo_owned_blobs?demo_id=${demo_id}`
    }
    fetch(fetch_url)
        .then(response => response.json())
        .then(data => {
            for (const blobset of data.sets) {
                if (blobset.name == set) {
                    for (const blobPos in blobset.blobs) {
                        if (blobPos === pos) {
                            blob = blobset.blobs[blobPos]
                            blob_id = blob.id
                            console.log(blob);
                            vrVisibility(blob);
                        }
                    }
                }
            }
        });

    update_edit_demo();
    var form = document.getElementById('editBlobForm');
    form.onsubmit = function (e) {
        e.preventDefault();
        var formData = new FormData();
        formData.append('old_set', set)
        formData.append('old_pos', pos)
        formData.append('Title', $('#title').val());
        formData.append('SET' , $('#set').val());
        formData.append('PositionSet', $('#positionSet').val());
        formData.append('Credit', $('#credit').val());
        formData.append('demo_id', demo_id);
        if (VRImage) {
            formData.append('VR', VRImage, VRImage.name);
        }
        formData.append('csrfmiddlewaretoken', csrftoken);
        if (template_id) {
            formData.append('template_id', template_id);
            url = `detailsBlob/ajax_template`
        } else {
            formData.append('demo_id', demo_id);
            url = `detailsBlob/ajax_demo`
        }
        $.ajax({
            url: url,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            type: 'POST',
            dataType : 'json',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = "/cp2/showBlobsDemo?demo_id="+demo_id;
                } else {
                    alert("Error to add this Blob to the Template")
                }
            },
        })
    }
});

function update_edit_demo() {
    $.ajax({
        data: ({
            demoID: demo_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        dataType : 'json',
        type: 'POST',
        url: 'showDemo/ajax_user_can_edit_demo',
        success: function(data) {
            if (data.can_edit === 'NO') {
                alert("You are not allowed to edit this blob")
                $('#ButtonAddBlob').remove(); 
                $('#removeVR').remove();
            }

        },
    });
};
function vrVisibility (blob) {
    if (blob.vr) {
        document.getElementById("thumbnail_vr").src = blob.vr;
        document.getElementById("thumbnail_vr").style = "visibility : visible"
    }
    else {
        document.getElementById("thumbnail_vr").style = "visibility : hidden"
    }
}

$('#removeVRFile').click(function () {
    document.getElementById('VR').value = "";
    document.getElementById("thumbnail_vr").style = "visibility : hidden"
})

$("#removeVR").click(function(event) {
    event.preventDefault()
    $.ajax({
        beforeSend: function(xhr, settings) {
            delvr = confirm(`Deleting visual representation will afect other demos and templates using this blob.\nAre you sure you want to continue?`);
            console.log(blob_id)
            return delvr
        },
        data : ({
            blob_id : blob_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        type: 'POST',
        dataType: 'json',
        url: `detailsBlob/ajax_remove_vr`,
        success: function(data) {
            document.location.reload();
        },
    });
});