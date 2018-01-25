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

/*  delete demo extra  */
function send_delete_demo_extra_request(wsurl, demo_id) {
	var delextra = confirm('Delete the demo extras of demo ' + demo_id + '?');
	if (delextra == true) {
		$.ajax({
			type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                window.location.reload(true);
            },
            error: function(data){
                alert("Failure with error: "+data.status)
            }
        });
	}
}

/*  change the name of the submitted file  */
window.fileName = function(){
	var x = document.getElementById("file");
	if (!x.files[0].type.includes('zip') && !x.files[0].type.includes('x-rar') || x.files[0].type == '') {
		alert('DemoExtras file format not valid, try again');
		document.getElementById("name").innerHTML = "File...";
		document.getElementById("name").style.color = "grey";
		x.value = "";
	}
	if ('files' in x && x.files.length > 0) {
		txt = x.files[0].name;
		if (txt.length>24){
		    txt = txt.substring(0,22);
			txt += "..."
		}
		document.getElementById("name").innerHTML = txt;
		document.getElementById("submitButton").style.visibility="visible";
		document.getElementById("name").style.color="black";
	}else{
		document.getElementById("submitButton").style.visibility="hidden";
	}
}

