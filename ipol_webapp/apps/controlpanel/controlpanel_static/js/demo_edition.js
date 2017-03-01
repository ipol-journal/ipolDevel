/************ global variables ************/

/************ modal demo ************/
$modal_demo_msg_div='#createdemo_modal_errordiv';
$modal_demo_id='#createDemoFormModalId';
$modal_demo_header='div#createDemoModalheader';
$form_demo_id='#Demoform';
//hidden
$form_demo_field_demo_id="#Demoform #id_id";
//normal
$form_demo_field_editorsdemo_id="#Demoform #id_editorsdemoid";
$form_demo_field_title_id="#Demoform #id_title";
$form_demo_field_abstract_id="#Demoform #id_abstract";
$form_demo_field_zipURL_id="#Demoform #id_zipURL";
$form_demo_field_state="#Demoform #id_state";
var $demoform = $($form_demo_id);

/************ js error msgs ************/
$ws_down = "Please check if the webservices are running, in the status page.";


/************ Ace JSON Editor ************/
// Editor configuration
$editor = ace.edit("editor");
$editor.getSession().setMode("ace/mode/json");
$editor.getSession().setUseWrapMode(true);
$editor.getSession().setTabSize(4);
// Element to display errors when the JSON is invalid
$DDL_error_msg = document.getElementById('DDL_error_msg');
// div containing the JSON editor
$editorDiv = document.getElementById('editor');
// hidden input in the form where copy the JSON from the editor
$DDL_input = document.getElementById('ddlJSON');

// validate JSON DDL, and submit via AJAX if it is OK
function submitDDL(){
    // >0 if errors found, =0 if JSON is OK
    var json_is_valid = $editor.getSession().getAnnotations().length;
    var editor_value = $editor.getValue();

    // check syntax, and also if it is not empty
    if (json_is_valid == 0 && editor_value != ''){
        // copy the value from editor, to the 'ddlJSON' input in the form
        $DDL_input.value = $editor.getValue();
        // hide error message, to indicate it is OK
        $DDL_error_msg.style.display='none';
        // submit the DDL via AJAX
        submitDDLformAJAX();

    }else{
        // show message to indicate errors
        $DDL_error_msg.style.display='block';
    }
}


//  find errors if WS response is KO
function find_ws_errors(data) {
    var error_msg = null;

    if (data.code){
        error_msg = "code: " + data.code;
    }
    if (data.error){
        error_msg = "error: " + data.error;
    }
    console.log("error_msg: " + error_msg)
    return error_msg
}


/************ CSRF check ************/

// secure AJAX POST to ws ,from django docs
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


/************ DDL Form ************/

// submit DDL form
function submitDDLformAJAX(){
    var csrftoken = getCookie('csrftoken');
    var $ddl_form = $('#DDLform');
    // serialized data from the form
    var $serializedData = $($ddl_form).serialize();
    // URL to submit the data
    var $ajaxurl = $ddl_form.attr("action");

    $.ajax({
        url: $ajaxurl,
        type: "POST",
        // dataType: "json",
        data: $serializedData,
        success: function(data) {
            console.log("AJAX CALL status: "+data.status);
            if (data.status == "OK") {
                alert('DDL succesfully saved');
                window.location.reload(true);
            }else {
                console.log("status KO");
                alert('Could not save the DDL.\nStatus: \'' + data.status + '\'');
            }
        },
        error: function () {
            console.log("ajax error");
            alert('Error saving the DDL: ' + $ws_down);
        }
    });
}


/************ Demo Form ************/

//  delete demo
//  todo: change browser dialogs for confirm, use http://jqueryui.com/dialog/
/*
parameters:
    wsurl: address of the service to call
    demo_editorsdemoid: ID of the demo to delete
    demo_title: title of the demo to delete
    redirect_url: URL to redirect after deletion of the demo
*/
function send_delete_demo_request(wsurl, demo_editorsdemoid, demo_title, redirect_url) {

    var deldemo = confirm("WARNING: this operation will remove completely demo with editor's id: "+
            demo_editorsdemoid + " ("+ demo_title +") and all its associated data from the system. " +
            "\n\nNote that you can, instead, change the state of the demo to testing, which is 'safe'.");

    if (deldemo == true) {
        var deldemo2 = confirm( "Are you sure to delete completely this demo? " +
            "\nPlease confirm if you want to remove it from the system");

        if (deldemo2 == true) {
            $.ajax({
                type: 'POST',
                url: wsurl,
                dataType: 'json',
                success: function(data) {
                    console.log(data.status);
                    alert('Demo ' + demo_editorsdemoid + ' deleted succesfully');
                    // after the deletion, redirect to given URL (list of demos)
                    window.location.replace(redirect_url);
                },
                error: function(data){
                    console.error(data.status);
                    alert('Demo not deleted: ' + $ws_down);
                }
            });
        }
    }
}

// show/edit Demo modal
function send_get_demo_request(wsurl,editor_demo_id){
    console.log(wsurl);
    console.log(editor_demo_id);

    if (editor_demo_id === undefined) {
        console.log("send_get_demo_request  editor_demo_id === undefined");
        // editor_demo_id was not passed, just open create modal
        $($modal_demo_header).html('<h3>New Demo data</h3>');
        //clear data
        $($modal_demo_msg_div).html('');
        $($form_demo_field_demo_id).get(0).value = '';
        $($form_demo_field_editorsdemo_id).get(0).value = '';
        $($form_demo_field_title_id).get(0).value = '';
        $($form_demo_field_abstract_id).get(0).value = '';
        $($form_demo_field_zipURL_id).get(0).value = '';
        $($form_demo_field_state).get(0).value = '';
        $demoform.show();
        $($modal_demo_id).modal('show');

    }else{
        // wsurl was passed, get data from ws and open show modal
        console.log("send_get_demo_request");
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                console.log(data.status);
                console.log(data);

                if (data.status=='OK'){
                    //clear modal  error
                    $($modal_demo_msg_div).html('');

                    //edit/show demo
                    if ( data.editorsdemoid ){
                        console.log(" Get form demo data");
                        //Load ddl data in form
                        //console.log(data.last_demodescription);
                        //clear error data
                        $($modal_demo_msg_div).html('');
                        console.log(" Get form 2");
                        $($modal_demo_header).html('<h3>Edit Demo data</h3>');
                        //  $($form_ddl_field_demo_id).get(0).value = demo_id;
                        //  $($form_ddl_field_ddl_id).get(0).value = data.last_demodescription.id;
                        //  $($form_ddl_field_ddljson).get(0).value = $.parseJSON(data.last_demodescription.json);
                        console.log(" Get form 3");
                        $($form_demo_field_demo_id).get(0).value = data.editorsdemoid;
                        console.log(" Get form 3.1");

                        $($form_demo_field_editorsdemo_id).get(0).value = data.editorsdemoid;
                        console.log(" Get form 3.2");

                        $($form_demo_field_title_id).get(0).value = data.title;
                        console.log(" Get form 4");
                        $($form_demo_field_abstract_id).get(0).value = data.abstract;
                        $($form_demo_field_zipURL_id).get(0).value = data.zipURL;
                        $($form_demo_field_state).get(0).value = data.state;
                        console.log(" Get form 5");
                        $($modal_demo_id).modal('show');
                        console.log(" Get form 6");
                        $demoform.show();

                    //create demo
                    }else{
                        console.log("error no demoid in form ");
                        //error, no OK
                        var errorhtml="<p class=\"ststsnok\">Demo Data not retrieved sucessfully, check demoinfo consistency</p>";
                        $($modal_demo_msg_div).html(errorhtml);
                        //clear form data
                        $($form_demo_field_demo_id).get(0).value = '';
                        $($form_demo_field_editorsdemo_id).get(0).value = '';
                        $($form_demo_field_title_id).get(0).value = '';
                        $($form_demo_field_abstract_id).get(0).value = '';
                        $($form_demo_field_zipURL_id).get(0).value = '';
                        $($form_demo_field_state).get(0).value = '';
                        $($modal_demo_id).modal('show');
                        //$demoform.show();
                    }
                }else{
                    //error, not OK
                    console.log(" Error, ws returned KO");

                    $error_msg=find_ws_errors(data);
                    var errorhtml="<p class=\"ststsnok\">Demo not retrieved sucessfully, ws returned "+$error_msg+"</p>";
                    $($modal_demo_id).modal('show');
                    $demoform.hide();
                    $($modal_demo_msg_div).html(errorhtml);
                }
            },
            error: function(data){
                var errorhtml="<p class=\"ststsnok\">Error getting Demo: "+$ws_down+"</p>";
                $($modal_demo_msg_div).html(errorhtml);
                $($modal_demo_id).modal('show');
                $demoform.hide();
            }
        });
    }
}

// submit Demo form
function submitDemoformAJAX(){

    console.log("submitDemoformAJAX Submit");

    var csrftoken = getCookie('csrftoken');
    var $serializedData = $demoform.serialize();
    var $ajaxurl = $demoform.attr("action");

    console.log($ajaxurl);

    $.ajax({
        url: $ajaxurl,
        type: "POST",
        // dataType: "json",
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
            var errorhtml="<p class=\"ststsnok\">Error saving Demo: "+$ws_down+"</p>";
            $($modal_demo_msg_div).html(errorhtml);
            $($modal_demo_id).modal('show');
            $demoform.hide();
        }
    });
}

//  Demo form validation
$($form_demo_id).validate({
    errorClass: "validationerror",//for css
    rules: {
        title: {
            required: true,
            minlength: 5
        },
        abstract: {
            required: true,
            minlength: 5
        },
        state: {
            required: true
        },
        editorsdemoid: {
            required: true
        },
        zipURL: {
            required: true,
            minlength: 5
        }
    },
    messages: {

        title: {
            required: "please fill title field",
            minlength: "Your title must be at least 5 characters"
        },
        abstract: {
            required: "please fill abstract field",
            minlength: "Your abstract must be at least 5 characters"
        },
        state: {
            required: "please fill  state"
        },
        editorsdemoid: {
            required: "please fill  editorsdemoid"
        },
        zipURL: {
            required: "please fill zipURL field",
            minlength: "Your zipURL must be at least 5 characters"
        }
    },
    submitHandler: function() {
        console.log("validated ok submitDemoformAJAX");
        // your ajax loading logic
        // form.submit(); // use this to finally submit form data at the last step
        submitDemoformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});
