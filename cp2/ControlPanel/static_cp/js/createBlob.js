var VRImage;
var csrftoken = getCookie('csrftoken');
var blobImage;
var templateSelection = getParameterByName('template');

$(document).ready(function() {
    if (templateSelection) {
        document.getElementById("nameOfTemplate").innerHTML = templateSelection;
        $("#goPreviousPage").attr('href', '/cp2/showTemplates?template=' + templateSelection);
        var form = document.getElementById('createBlobForm');
        form.onsubmit = function(e) {
            e.preventDefault();
            var formData = new FormData();
            formData.append('Title', $('#Title').val());
            formData.append('SET', $('#SET').val());
            formData.append('PositionSet', $('#PositionSet').val());
            formData.append('Credit', $('#Credit').val());
            formData.append('Tags', $('#Tags').val());
            formData.append('TemplateSelection', templateSelection);
            formData.append('Blobs', blobImage, blobImage.name);
            if (VRImage) {
                formData.append('VR', VRImage, VRImage.name);
            }
            formData.append('csrfmiddlewaretoken', csrftoken);
            $.ajax({
                url: 'createBlob/ajax',
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                type: 'POST',
                dataType: 'json',
                success: function(data) {
                    if (data.status === 'OK') {
                        document.location.href = "/cp2/showTemplates?template=" + templateSelection
                    } else {
                        alert("Error to add this Blob to the Template")
                    }
                },
            })
        }
    } else {
        var demo_id = getParameterByName('demo_id');
        document.getElementById("nameOfTemplate").innerHTML = demo_id;
        $("#goPreviousPage").attr("href", "/cp2/showBlobsDemo?demo_id=" + demo_id)
        update_edit_demo();
        var form = document.getElementById('createBlobForm');
        form.onsubmit = function(e) {
            e.preventDefault();
            var formData = new FormData();
            formData.append('Title', $('#Title').val());
            formData.append('SET', $('#SET').val());
            formData.append('PositionSet', $('#PositionSet').val());
            formData.append('Credit', $('#Credit').val());
            formData.append('Tags', $('#Tags').val());
            formData.append('demo_id', demo_id);
            formData.append('Blobs', blobImage, blobImage.name);
            if (VRImage) {
                formData.append('VR', VRImage, VRImage.name);
            }
            formData.append('csrfmiddlewaretoken', csrftoken);
            $.ajax({
                url: 'createBlob/ajax_demo',
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                type: 'POST',
                dataType: 'json',
                success: function(data) {
                    if (data.status === 'OK') {
                        document.location.href = "/cp2/showBlobsDemo?demo_id=" + demo_id
                    } else {
                        alert("Error to add this Blob to the demo")
                    }
                },
            })
        }

        function update_edit_demo() {
            $.ajax({
                data: ({
                    demoID: demo_id,
                    csrfmiddlewaretoken: csrftoken,
                }),
                dataType: 'json',
                type: 'POST',
                url: 'showDemo/ajax_user_can_edit_demo',
                success: function(data) {
                    if (data.can_edit === 'NO') {
                        alert("You are not allowed to edit this blob")
                        $('#ButtonAddBlob').remove();
                    }

                },
            });
        };
    }
});