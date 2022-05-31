let demo_id = getParameterByName('demo_id');
var csrftoken = getCookie('csrftoken');


$(".experiment-info>button.btn-danger").click(function (element) {
    let experiment_id = $(this).attr('data-id');

    $.ajax({
        data: ({
            demo_id: demo_id,
            experiment_id: experiment_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        dataType: 'json',
        type: 'POST',
        url: 'ajax_delete_experiment',
        success: function(data) {
            if (data.status == 'OK') {
                window.location.reload();
            } else {

            }
        },
    }); 

});