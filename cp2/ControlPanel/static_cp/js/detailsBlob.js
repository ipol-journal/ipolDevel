var csrftoken = getCookie('csrftoken');
var VRImage;
var completeURL = document.location.href;
var decoded = decodeURI(completeURL);
var demo_id = getParameterByName('demo_id');
var title = getParameterByName('title');
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
        fetch_url = `${location_url}/api/blobs/templates/${template_id}`
    } else {
        fetch_url = `${location_url}/api/blobs/demo_owned_blobs/${demo_id}`
    }
    fetch(fetch_url)
        .then(response => response.json())
        .then(sets => {
            for (const blobset of sets) {
                if (blobset.name == set) {
                    for (const blobPos in blobset.blobs) {
                        if (blobPos === pos) {
                            blob = blobset.blobs[blobPos]
                            blob_id = blob.id
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
        if (isNaN($('#positionSet').val())) {
            alert("PositionSet has to be an integer");
            return;
        }
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
            success: function(data, responseText, xhr) {
                if (xhr.status == 200) {
                    if (template_id) {
                        document.location.href = `showTemplate?template_id=${template_id}&template_name=${template_name}`;
                    } else {
                        document.location.href = `showBlobsDemo?demo_id=${demo_id}`;
                    }
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
        // Vr file modification time query parameter to avoid browser cache
        document.getElementById("thumbnail_vr").src = `${blob.vr}?${blob.vr_mtime}`;
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
