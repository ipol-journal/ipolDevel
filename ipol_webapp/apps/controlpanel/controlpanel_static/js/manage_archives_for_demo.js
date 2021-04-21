/*  secure AJAX POST to ws ,from django docs  */
function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}
function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$(document).ready(function(){
	var csrftoken = getCookie('csrftoken');
	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});
});

/*  delete experiment  */
function send_delete_experiment_request(wsurl, experiment_id) {
	var delexp = confirm('Delete experiment ' + experiment_id + '?\nThe items will be deleted permanently');
	if (delexp == true) {
		$.ajax({
			type: 'GET',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                if(data.status != 'OK')
                    alert('Failed to delete the experiment ' + experiment_id );
                window.location.reload();
            },
            error: function(data){
                alert('Failed to delete the experiment ' + experiment_id )
            }
        });
	}
}

