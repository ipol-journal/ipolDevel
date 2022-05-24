var templates_used = [];
var csrftoken = getCookie('csrftoken');
var section = document.querySelector('section');
var demo_id = getParameterByName('demo_id');
var templateSelection;

function add_template_to_demo(selected_template) {
    $.ajax({
        data: ({
            demo_id: demo_id,
            template_id: selected_template.value,
            csrfmiddlewaretoken: csrftoken,
        }),
        url: 'showBlobsDemo/ajax_add_template_to_demo',
        type: 'POST',
        dataType: 'json',
        success: function(data) {
            if (data.status === 'OK') {
                // add_the_template();
                window.location.reload();
            } else {
                alert("Error to added the template to this demo or any template selected")
            }
        },
    })
};

$("button.unlink-template").click(function () {
    let template_id = $(this).attr('data-template-id');
    $.ajax({
        data: ({
            demo_id: demo_id,
            template_id: template_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        url: 'showBlobsDemo/ajax_remove_template_to_demo',
        type: 'POST',
        dataType: 'json',
        success: function(data) {
            if (data.status === 'OK') {
                document.location.href = "/cp2/showBlobsDemo?demo_id=" + demo_id;
            } else {
                alert("Error to delete this template from the demo");
            }
        },
    })
});

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
                var not_allowed = document.createElement('h3');
                not_allowed.textContent = "You are not allowed to edit this demo"
                can_edit.appendChild(not_allowed);
                $('#buttonAddTemplate').remove();
                $('.buttonDelete').remove();
            }
        },
    }); 
};

$("button.btn-delete").click(function () {
    var blobSelection = $(this).attr('name');
    var pos_set = $(this).attr('blobpos');
    console.log(blobSelection, pos_set);
    $.ajax({
        beforeSend: function(xhr, settings) {
            return (confirm("Are you sure?"))
            },
        data : ({
            demo_id: demo_id,
            blob_set : blobSelection,
            pos_set : pos_set,
            csrfmiddlewaretoken: csrftoken,
        }),
        type: 'POST',
        dataType: 'json',
        url: 'removeBlob/ajax_remove_blob_from_demo',
        success: function(data) {
            if (data.status === 'OK') {
                document.location.href = `showBlobsDemo?demo_id=${demo_id}`
            } else {
                alert("Error to delete this Blob");
            }
        },
    })
});