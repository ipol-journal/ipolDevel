/*  global vars */

/*  modal author */
$modal_author_msg_div='#createauthor_modal_errordiv';
$modal_author_id='#createAuthorFormModalId';
$modal_author_header='div#createAuthorModalheader';

$form_author_id='#Authorform';
//hidden
$form_author_field_author_id="#Authorform #id_id";
//normal
$form_author_field_name_id="#Authorform #id_name";
$form_author_field_mail_id="#Authorform #id_mail";
var $authorform = $($form_author_id);

/*  js error msg*/
$ws_down=" please check if the webservices are running, in the Status page";

/*  secure AJAX POST to ws ,from django docs */
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

/*  delete author  */
function send_delete_author_request(wsurl,author_id) {
    var delauthor = confirm('Delete author ' + author_id + '?');

    if (delauthor == true) {
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                console.log(data.status);
                var okhtml="<p class=\"ststsok\">Author deleted</p>";
                $('#author_info_'+ author_id).html(okhtml);
                //todo better to only reload part of list, but shoul change django pagination for js pagination
                window.location.reload(true);
            },
            error: function(data){
                console.error(data.status);
                var errorhtml="<p class=\"ststsnok\">Author not deleted, "+$ws_down+"</p>";
                $('#author_info_'+ author_id).html(errorhtml);
            }
        });
    }
}


/*  show/edit author modal  */
function send_get_author_request(wsurl,author_id){
    console.log(wsurl);
    console.log(author_id);

    if (author_id === undefined) {
        // author_id was not passed, just open create modal
        $($modal_author_header).html('<h3>New author</h3>');
        //clear data
        $($modal_author_msg_div).html('');

        $($form_author_field_author_id).get(0).value = '';
        $($form_author_field_name_id).get(0).value = '';
        $($form_author_field_mail_id).get(0).value = '';


        $authorform.show();
        $($modal_author_id).modal('show');
    }else{
        // wsurl was passed, get data from ws and open show modal
        console.log("send_get_author_request");
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {

                console.log(data.status);

                if (data.status=='OK'){
                    //clear modal  error
                    $($modal_author_msg_div).html('');

                    //edit/show Author
                    if ( data.id ){

                        console.log(" Get form Author data");
                        //Load ddl data in form
                        //console.log(data.last_demodescription);
                        //clear error data
                        $($modal_author_msg_div).html('');

                        $($modal_author_header).html('<h3>Edit Author</h3>');
                        $($form_author_field_author_id).get(0).value = data.id;
                        $($form_author_field_name_id).get(0).value = data.name;
                        $($form_author_field_mail_id).get(0).value = data.mail;

                        $($modal_author_id).modal('show');
                        $authorform.show();

                    //create Author
                    }else{
                        console.log("error no authorid in form ");
                        //error, no OK
                        var errorhtml="<p class=\"ststsnok\">Author data not retrieved, check DemoInfo consistency</p>";
                        $($modal_author_msg_div).html(errorhtml);
                        //clear form data
                        $($form_author_field_author_id).get(0).value = '';
                        $($form_author_field_name_id).get(0).value = '';
                        $($form_author_field_mail_id).get(0).value = '';

                        $($modal_author_id).modal('show');
                        //$authorform.show();
                    }
                }else{
                    //error, no OK
                    var errorhtml="<p class=\"ststsnok\">Author not retrieved, "+$ws_down+"</p>";
                    $($modal_ddl_msg_div).html(errorhtml);
                }
            },
            error: function(data){
                var errorhtml="<p class=\"ststsnok\">Error getting Author, "+$ws_down+"</p>";
                $($modal_author_msg_div).html(errorhtml);
                $($modal_author_id).modal('show');
                $authorform.hide();
            }
        });
    }
}


/*  submit Author form  */
function submitAuthorformAJAX(){

    console.log("submitAuthorformAJAX Submit");
    var csrftoken = getCookie('csrftoken');
    var $serializedData = $authorform.serialize();
    var $ajaxurl = $authorform.attr("action");
    console.log($ajaxurl);
    console.log($serializedData);

    $.ajax({
        url: $ajaxurl,
        type: "POST",
        /* dataType: "json",*/
        data: $serializedData,
        success: function(data) {

            console.log("AJAX CALL status: "+data.status);
            if (data.status == "OK") {
                $($modal_author_msg_div).html('Author saved').show();
                $authorform.hide();
                //todo better to only reload part of list, but shoul change django pagination for js pagination
                window.location.reload(true);
            }
            else {

                $authorform.show();
                if (data.error){
                    var errorhtml="<p class=\"ststsnok\">Author not saved, error: "+data.error+"</p>";
                    $($modal_author_msg_div).html(errorhtml).show();
                }else{
                    var errorhtml="<p class=\"ststsnok\">Author not saved, undefined error</p>";
                    $($modal_author_msg_div).html(errorhtml).show();
                }


            }
        },
        error: function () {
            console.log("ajax error");
            var errorhtml="<p class=\"ststsnok\">Error saving Author, "+$ws_down+"</p>";
            $($modal_author_msg_div).html(errorhtml);
            $($modal_author_id).modal('show');
            $authorform.hide();
        }
    });
}

/*  Author form validation */
$($form_author_id).validate({
    errorClass: "validationerror",//for css
    rules: {
        name: {
            required: true,
            minlength: 5
        },
        mail: {
            required: true,
            minlength: 5
        }
    },
    messages: {
        name: {
            required: "please fill name field",
            minlength: "Your name must be at least 5 characters"
        },
        mail: {
            required: "please fill mail field",
            minlength: "Your mail must be at least 5 characters"
        }
    },
    submitHandler: function() {
        console.log("validated ok submitAuthorformAJAX");
        // your ajax loading logic
        // form.submit(); // use this to finally submit form data at the last step
        submitAuthorformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});

