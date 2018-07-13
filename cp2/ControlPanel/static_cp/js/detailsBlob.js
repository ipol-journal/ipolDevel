var csrftoken = getCookie('csrftoken');
var VRImage;
var completeURL = document.location.href;
var decoded = decodeURI(completeURL);
var templateSelection = getParameterByName('template');
var pos = getParameterByName('pos');
var set = getParameterByName('set');
var vr;
var blob_id;
var demo_id;

$(document).ready(function(){
    var get_demo_blobs = new XMLHttpRequest();
    var previousPage = document.getElementById("goPreviousPage");
    if (templateSelection) {
        previousPage.setAttribute("href", "/cp2/showTemplates?template="+templateSelection);
         get_demo_blobs.open('GET', '/api/blobs/get_template_blobs?template_name='+templateSelection);
         get_demo_blobs.responseType = 'json';
         get_demo_blobs.send();
         get_demo_blobs.onload = function() {
             var templates = get_demo_blobs.response;
             var sets = templates['sets']
             showDetails(sets);
         }
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
                    document.location.href = "/cp2/showTemplates?template="+templateSelection
                } else {
                    alert("Error to add this Blob to the Template")
                }
            },
        });
    }}
    else {
        demo_id = getParameterByName('demo_id')
        previousPage.setAttribute("href", "/cp2/showBlobsDemo?demo_id="+demo_id)
        get_demo_blobs.open('GET', '/api/blobs/get_demo_owned_blobs?demo_id='+demo_id);
        get_demo_blobs.responseType = 'json';
        get_demo_blobs.send();
        get_demo_blobs.onload = function() {
            var demo_list = get_demo_blobs.response;
            var sets = demo_list['sets']
            showDetails(sets);
        }

        update_edit_demo();
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
        formData.append('demo_id', demo_id);
        if (VRImage) {
            formData.append('VR', VRImage, VRImage.name);
        }
        formData.append('csrfmiddlewaretoken', csrftoken);
        $.ajax({
            url: 'detailsBlob/ajax_demo',
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
    }}
    $("#thumbnail").click(function () {
        window.location = blob;
    });
    $('#thumbnail_vr').click(function (){
        if (vr){
            window.location = vr ;
        }
    })
});

function showDetails(sets) {
    for (var i = 0; i < sets.length; i++) {
        var Blobs = sets[i].blobs;
        var set_keys = Object.keys(Blobs);
            for (let blob_pos of set_keys ) {
                var detailsBlob = Blobs[blob_pos];
                if (sets[i].name == set & blob_pos == pos) {
                    console.log("title="+detailsBlob.title+"\nset="+sets[i].name+"\npos="+blob_pos+"\ncredit="+detailsBlob.credit+"\ntags="+detailsBlob.tags+"\nthumbnail="+detailsBlob.thumbnail+"\nvr="+detailsBlob.vr+"\nblob="+detailsBlob.blob+"\nid="+detailsBlob.id);
                    document.getElementById("setName").textContent = sets[i].name;
                    document.getElementById("Title").value = detailsBlob.title;
                    document.getElementById("SET").value = sets[i].name;
                    document.getElementById("PositionSet").value = blob_pos;
                    document.getElementById("Credit").value = detailsBlob.credit;
                    document.getElementById("Tags").value = detailsBlob.tags;
                    if (detailsBlob.vr){
                        document.getElementById("thumbnail_vr").src = detailsBlob.vr;
                        document.getElementById("thumbnail_vr").style = "visibility : visible"
                    }
                    else {
                        document.getElementById("thumbnail_vr").style = "visibility : hidden"
                    }
                    document.getElementById("thumbnail").src = detailsBlob.blob;
                    blob_id = detailsBlob.id
                    vr = detailsBlob.vr
                    blob = detailsBlob.blob
                }
            };
        };
    };

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
                $('#removeVr').remove();
            }

        },
    });
};






$(function() {
    $("#removeVr").click(function(event) {
        event.preventDefault()
        $.ajax({
            beforeSend: function(xhr, settings) {
                delvr = confirm('Deleting visual representation will afect other demos and templates.\nAre you sure you want to continue?');
                console.log(blob_id)
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
                document.location.reload();
            },
        });
    });
});