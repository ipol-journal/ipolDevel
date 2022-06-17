var VRImage;
var csrftoken = getCookie('csrftoken');
var blobImage;
var template_id = getParameterByName('template_id');
var template_name = getParameterByName('template_name');

$(document).ready(function() {
    if (template_id) {
        var form = document.getElementById('editBlobForm');
        form.onsubmit = function(e) {
            e.preventDefault();
            let formData = new FormData();
            formData.append('Title', $('#title').val());
            formData.append('SET', $('#set').val());
            formData.append('PositionSet', $('#positionSet').val());
            formData.append('Credit', $('#credit').val());
            formData.append('Tags', $('#tags').val());
            formData.append('TemplateSelection', template_id);
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
                        document.location.href = `showTemplates?template_id=${template_id}&template_name=${template_name}`
                    } else {
                        alert("Error to add this Blob to the Template")
                    }
                },
            })
        }
    } else {
        let demo_id = getParameterByName('demo_id');
        update_edit_demo();
        var form = document.getElementById('editBlobForm');
        form.onsubmit = function(e) {
            e.preventDefault();
            var formData = new FormData();
            formData.append('Title', $('#title').val());
            formData.append('SET', $('#set').val());
            formData.append('PositionSet', $('#positionSet').val());
            formData.append('Credit', $('#credit').val());
            formData.append('Tags', $('#tags').val());
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
                        document.location.href = "showBlobsDemo?demo_id=" + demo_id
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