/*  global vars */

/*  modal demo */
$modal_demo_msg_div='#createdemo_modal_errordiv';
$modal_demo_id='#createDemoFormModalId';
$modal_demo_header='div#createDemoModalheader';
$form_demo_id='#CreateDemoform';
//hidden
$form_demo_field_demo_id="#CreateDemoform #id_id";
$form_demo_field_editorsdemo_id="#CreateDemoform #id_editorsdemoid";
$form_demo_field_title_id="#CreateDemoform #id_title";
$form_demo_field_state="#CreateDemoform #id_state";
$form_demo_field_editor="#CreateDemoform #id_editor";
var $demoform = $($form_demo_id);


/*  modal ddl */
//$modal_ddl_msg_div='#createddl_modal_errordiv';
//$modal_ddl_id='#createDDLFormModalId';
//$modal_ddl_header='div#createDDLModalheader';
//$form_ddl_id='#DDLform';
//hidden
//$form_ddl_field_demo_id="#DDLform #id_demoid";

//normal
//$form_ddl_field_ddljson="#DDLform #id_ddlJSON";
//var $ddlform = $($form_ddl_id);

/*  js error msg*/
$ws_down=" check webservices are running, go to status page";
var $ws_error_msg="";

/*  find errors if WS response is KO */
function find_ws_errors(data) {
    var error_msg = null;

    if (data.code){
        error_msg = "code: " + data.code;
    }
    if (data.error){
        error_msg = "error: " + data.error;
    }
    console.log("error_msg" + error_msg)
    return error_msg
}

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

/*  delete demo  */
/*  todo change browdser dialogs for confirm, use http://jqueryui.com/dialog/  */
function send_delete_demo_request(wsurl, demo_id, demo_editorsdemoid, demo_title) {

    var deldemo = confirm("WARNING: this operation will remove completely demo with editor's id: "+
            demo_editorsdemoid + " ("+ demo_title +") and all associated data from the system. Please confirm " +
            "that this is what you really want. Note that you can instead change the state of the demo to testing, which is 'safe'.");
    if (deldemo == true) {

        var deldemo2 = confirm( "This is your last chance to cancel the total removal of the demo with editor's id: "+
            demo_editorsdemoid + " ("+ demo_title +") Please confirm that you want to totally remove it from the system");
        if (deldemo2 == true) {
            $.ajax({
                type: 'POST',
                url: wsurl,
                dataType: 'json',
                success: function(data) {
                    console.log(data.status);
                    var okhtml="<p class=\"ststsok\">Demo deleted succesfully</p>";
                    $('#demo_info_'+ demo_id).html(okhtml);
                    //todo better to only reload part of list, but shoul change django pagination for js pagination
                    window.location.reload(true);

                },
                error: function(data){
                    console.error(data.status);
                    var errorhtml="<p class=\"ststsnok\">Demo not deleted: "+$ws_down+"</p>";
                    $('#demo_info_'+ demo_id).html(errorhtml);
                }
            });
        }
    }
}

/*  show/edit Demo modal  */
function send_get_demo_request(wsurl){
    console.log("send_get_demo_request  editor_demo_id === undefined");
    // editor_demo_id was not passed, just open create modal
    $($modal_demo_header).html('<h3>New Demo data</h3>');
    //clear data
    $($modal_demo_msg_div).html('');
    $($form_demo_field_demo_id).get(0).value = '';
    $($form_demo_field_editorsdemo_id).get(0).value = '';
    $($form_demo_field_title_id).get(0).value = '';
    $($form_demo_field_state).get(0).value = '';
    $($form_demo_field_editor).get(0).value = '';
    $demoform.show();
    $($modal_demo_id).modal('show');
}

function validate(){
    var demo_id_validation =$($form_demo_field_editorsdemo_id).get(0).value
    var title_validation =$($form_demo_field_title_id).get(0).value
    var state_validation =$($form_demo_field_state).get(0).value
    var editor_validation =$($form_demo_field_editor).get(0).value
    if (demo_id_validation == ""){
        var errorhtml="<p class=\"ststsnok\">Demo ID required"+"</p>";
        $($modal_demo_msg_div).html(errorhtml).show();
        return false;
    }
    else if (title_validation == ""){
        var errorhtml="<p class=\"ststsnok\">Title is required</p>";
        $($modal_demo_msg_div).html(errorhtml).show();
        return false;
    }
    else if (title_validation.length < 5){
        var errorhtml="<p class=\"ststsnok\">Your title must be at least 5 characters</p>";
        $($modal_demo_msg_div).html(errorhtml).show();
        return false;
    }
    else if (state_validation == ""){
        var errorhtml="<p class=\"ststsnok\">State is required</p>";
        $($modal_demo_msg_div).html(errorhtml).show();
        return false;
    }
    else if (editor_validation == ""){
        var errorhtml="<p class=\"ststsnok\">Editor is required</p>";
        $($modal_demo_msg_div).html(errorhtml).show();
        return false;
    }
    return true
}

/*  submit Demo form  */
function submitDemoformAJAX(){

    console.log("submitDemoformAJAX Submit");

    var csrftoken = getCookie('csrftoken');
    var $serializedData = $demoform.serialize();
    var $ajaxurl = $demoform.attr("action");

    console.log($ajaxurl);
    if (!validate())return;
    $.ajax({
        url: $ajaxurl,
        type: "POST",
        /* dataType: "json",*/
        data: $serializedData,
        success: function(data) {

            console.log("AJAX CALL status: "+data.status);
            console.log("AJAX CALL error: "+data.error);
            console.log("AJAX CALL data: "+data);

            if (data.status == "OK") {
                $($modal_demo_msg_div).html('Demo saved').show();
                $demoform.hide();
                //todo better to only reload part of list, but should change django pagination for js pagination
                window.location.reload(true);
            }
            else {

                $demoform.show();

                console.log(" Error, ws returned KO");

                $error_msg = find_ws_errors(data);
                var errorhtml="<p class=\"ststsnok\">Demo not saved, ws returned  "+$error_msg+"</p>";
                $($modal_demo_msg_div).html(errorhtml).show();

            }
        },
        error: function () {
            console.log("ajax error");
            var errorhtml="<p class=\"ststsnok\">Error saving Demo, "+$ws_down+"</p>";
            $($modal_demo_msg_div).html(errorhtml);
            $($modal_demo_id).modal('show');
            $demoform.hide();
        }
    });
}


$($form_demo_id).validate({
    submitHandler: function() {
        console.log("validated ok submitDemoformAJAX");
        submitDemoformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});


