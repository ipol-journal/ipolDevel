/*  global vars */

/*  modal editor */
$modal_editor_msg_div='#createeditor_modal_errordiv';
$modal_editor_id='#createEditorFormModalId';
$modal_editor_header='div#createEditorModalheader';

$form_editor_id='#Editorform';
//hidden
$form_editor_field_editor_id="#Editorform #id_id";
//normal
$form_editor_field_name_id="#Editorform #id_name";
$form_editor_field_mail_id="#Editorform #id_mail";
var $editorform = $($form_editor_id);

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

/*  delete editor  */
function send_delete_editor_request(wsurl,editor_id) {
    var deleditor = confirm('Delete Editor ' + editor_id + '?');

    if (deleditor == true) {
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                console.log(data.status);
                var okhtml="<p class=\"ststsok\">Editor deleted</p>";
                $('#editor_info_'+ editor_id).html(okhtml);
                //todo better to only reload part of list, but shoul change django pagination for js pagination
                window.location.reload(true);
            },
            error: function(data){
                console.error(data.status);
                var errorhtml="<p class=\"ststsnok\">Editor not deleted, "+$ws_down+"</p>";
                $('#editor_info_'+ editor_id).html(errorhtml);
            }
        });
    }
}


/*  show/edit editor modal  */
function send_get_editor_request(wsurl,editor_id){
    console.log(wsurl);
    console.log(editor_id);

    if (editor_id === undefined) {
        // editor_id was not passed, just open create modal
        $($modal_editor_header).html('<h3>New editor data</h3>');
        //clear data
        $($modal_editor_msg_div).html('');

        $($form_editor_field_editor_id).get(0).value = '';
        $($form_editor_field_name_id).get(0).value = '';
        $($form_editor_field_mail_id).get(0).value = '';

        $editorform.show();
        $($modal_editor_id).modal('show');
    }else{
        // wsurl was passed, get data from ws and open show modal
        console.log("send_get_editor_request");
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {

                console.log(data.status);

                if (data.status=='OK'){
                    //clear modal  error
                    $($modal_editor_msg_div).html('');

                    //edit/show Editor
                    if ( data.id ){

                        console.log(" Get form Editor data");
                        //Load ddl data in form
                        //console.log(data.last_demodescription);
                        //clear error data
                        $($modal_editor_msg_div).html('');

                        $($modal_editor_header).html('<h3>Edit Editor data</h3>');
                        $($form_editor_field_editor_id).get(0).value = data.id;
                        $($form_editor_field_name_id).get(0).value = data.name;
                        $($form_editor_field_mail_id).get(0).value = data.mail;

                        $($modal_editor_id).modal('show');
                        $editorform.show();

                    //create Editor
                    }else{
                        console.log("error no editorid in form ");
                        //error, no OK
                        var errorhtml="<p class=\"ststsnok\">Editor data not retrieved, please check DemoInfo consistency</p>";
                        $($modal_editor_msg_div).html(errorhtml);
                        //clear form data
                        $($form_editor_field_editor_id).get(0).value = '';
                        $($form_editor_field_name_id).get(0).value = '';
                        $($form_editor_field_mail_id).get(0).value = '';

                        $($modal_editor_id).modal('show');
                        //$editorform.show();
                    }
                }else{
                    //error, no OK
                    var errorhtml="<p class=\"ststsnok\">Editor not retrieved, "+$ws_down+"</p>";
                    $($modal_ddl_msg_div).html(errorhtml);
                }
            },
            error: function(data){
                var errorhtml="<p class=\"ststsnok\">Error getting Editor, "+$ws_down+"</p>";
                $($modal_editor_msg_div).html(errorhtml);
                $($modal_editor_id).modal('show');
                $editorform.hide();
            }
        });
    }
}


/*  submit Editor form  */
function submitEditorformAJAX(){

    console.log("submitEditorformAJAX Submit");
    var csrftoken = getCookie('csrftoken');
    var $serializedData = $editorform.serialize();
    var $ajaxurl = $editorform.attr("action");
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
                $($modal_editor_msg_div).html('Editor saved').show();
                $editorform.hide();
                //todo better to only reload part of list, but shoul change django pagination for js pagination
                window.location.reload(true);
            }
            else {

                $editorform.show();
                if (data.error){
                    var errorhtml="<p class=\"ststsnok\">Editor not saved, error: "+data.error+"</p>";
                    $($modal_editor_msg_div).html(errorhtml).show();
                }else{
                    var errorhtml="<p class=\"ststsnok\">Editor not saved, undefined error</p>";
                    $($modal_editor_msg_div).html(errorhtml).show();
                }
            }
        },
        error: function () {
            console.log("ajax error");
            var errorhtml="<p class=\"ststsnok\">Error saving Editor, "+$ws_down+"</p>";
            $($modal_editor_msg_div).html(errorhtml);
            $($modal_editor_id).modal('show');
            $editorform.hide();
        }
    });
}

/*  Editor form validation */
$($form_editor_id).validate({
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
        console.log("validated ok submitEditorformAJAX");
        // your ajax loading logic
        // form.submit(); // use this to finally submit form data at the last step
        submitEditorformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});

