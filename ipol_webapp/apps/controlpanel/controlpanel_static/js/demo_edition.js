/************ global variables ******/

/************ modal demo ************/
$modal_demo_msg_div='#createdemo_modal_errordiv';
$modal_demo_id='#createDemoFormModalId';
$modal_demo_header='div#createDemoModalheader';
$form_demo_id='#UpdateDemoform';
//hidden
$form_demo_field_demo_id="#UpdateDemoform #id_id";
//normal
$form_demo_field_editorsdemo_id="#UpdateDemoform #id_editorsdemoid";
$form_demo_field_title_id="#UpdateDemoform #id_title";
$form_demo_field_state="#UpdateDemoform #id_state";
var $demoform = $($form_demo_id);

/************ js error msgs *********/
$ws_down = "Please check if the webservices are running, in the status page.";

/************ Ace JSON Editor *******/
// Editor configuration
$editor = ace.edit("editor");
$editor.getSession().setMode("ace/mode/json");
$editor.getSession().setUseWrapMode(true);
$editor.getSession().setTabSize(4);
$editor.setAutoScrollEditorIntoView(true);

// Element to display messages about the DDL
$DDL_msg = document.getElementById('DDL_msg');
// Last version of DDL saved
last_DDL_saved = $editor.getValue();

// disable Save button, at the beginning
//disableSaveButton(true);

checkChanges();

// when changed the DDL in the editor, check if it is equal to the version saved
$editor.on("input", function() {
    checkChanges();
});

// check for unsaved changes in the DDL, and show a message in that case
function checkChanges(){
    // compare the last saved DDL with the current DDL in the editor
    if (last_DDL_saved.localeCompare($editor.getValue()) != 0){
        disableSaveButton(false);
        setDDLMessage('', 'There are unsaved changes.');
    }else{
        disableSaveButton(true);
        setDDLMessage('', 'DDL already saved.');
    }
}


// validate JSON DDL, and submit via AJAX if it is OK
function submitDDL(submit_URL){
    disableSaveButton(true);

    // >0 if errors found, ==0 if JSON is OK
    var json_is_valid = $editor.getSession().getAnnotations().length;
    var editor_value = $editor.getValue();

    // check syntax and it is not empty
    if (json_is_valid == 0 && editor_value != ''){
        // submit the DDL via AJAX
        setDDLMessage('', 'Saving...');
        submitDDLAJAX(submit_URL);
        disableSaveButton(false);
    }else{
        // show message to indicate errors
        setDDLMessage('KO', 'DDL not saved, please check the syntax.');
        disableSaveButton(false);
    }
}

// sets the given class and message, to the DDL Editor message
function setDDLMessage(msg_type, msg){
    if (msg_type == 'KO'){
        new_class = 'ststsnok';
    }else if(msg_type == 'OK'){
        new_class = 'ststsok';
    }else{
        new_class = 'ststsnormal';
    }

    // set the class to change color, etc
    $DDL_msg.className = new_class;
    $DDL_msg.style.display = 'initial';
    // set the message to the element
    $DDL_msg.innerHTML = msg;
}

// disables the Save DDL button when it is
// already saved, or while is being saved
function disableSaveButton(arg){
    // button to save the DDL
    $save_btn = document.getElementById('save-DDL-btn');

    if (arg == true){
        $save_btn.className += " btn-disabled";
    }else{
        $save_btn.classList.remove("btn-disabled");
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

    // use JQuery to refresh the editor when its container div is resized
    $( "#editor" ).resizable({
        resize: function( event, ui ) {
            $editor.resize();
        }
    });
});


/************ DDL Form ************/

// submit DDL form
function submitDDLAJAX(submit_URL){
    var csrftoken = getCookie('csrftoken');

    // Demo ID value
    var demoid_value = document.getElementById('demoid').value;
    // DDL value
    var DDL_value = $editor.getValue();
    // serialize data before send
    var $serializedData = $.param({demoid: demoid_value, ddlJSON: DDL_value });
    // URL to submit the data
    var $ajaxurl = submit_URL;

    $.ajax({
        url: $ajaxurl,
        type: "POST",
        // dataType: "json",
        data: $serializedData,
        success: function(data) {
            console.log("AJAX CALL status: "+data.status);
            if (data.status == "OK") {
                setDDLMessage('OK', 'DDL succesfully saved.');
                last_DDL_saved = DDL_value;
                disableSaveButton(true);
            }else {
                console.log("status KO");
                setDDLMessage('KO', 'Could not save the DDL. Status: \'' + data.status + '\'.');
            }
        },
        error: function () {
            console.log("ajax error");
            setDDLMessage('KO', 'Error saving the DDL: ' + $ws_down);
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

    var deldemo = confirm("You're about to delete this demo."+
    " Note that this operation is not reversible and all its data will be lost.");

    if (deldemo == true) {
        var deldemo2 = confirm( "Please confirm that you indeed want to remove this demo."+
        " This is the last opportunity to cancel before irreversible deletion.");

        if (deldemo2 == true) {
            $.ajax({
                type: 'POST',
                url: wsurl,
                dataType: 'json',
                success: function(data) {
                    console.log(data.status);
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
                        //Load ddl data in form
                        //clear error data
                        $($modal_demo_msg_div).html('');
                        $($modal_demo_header).html('<h3>Edit Demo data</h3>');
                        //  $($form_ddl_field_demo_id).get(0).value = demo_id;
                        //  $($form_ddl_field_ddl_id).get(0).value = data.last_demodescription.id;
                        //  $($form_ddl_field_ddljson).get(0).value = $.parseJSON(data.last_demodescription.json);
                        $($form_demo_field_demo_id).get(0).value = data.editorsdemoid;
                        $($form_demo_field_editorsdemo_id).get(0).value = data.editorsdemoid;
                        $($form_demo_field_title_id).get(0).value = data.title;
                        $($form_demo_field_state).get(0).value = data.state;
                        $($modal_demo_id).modal('show');
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
                $new_demo_id = document.getElementById('id_editorsdemoid').value;
                $old_demo_id = document.getElementById('id_id').value;
                $demoform.hide();

                // check if demo id has changed, and redirect to the new URL, if it is the case
                if($new_demo_id == $old_demo_id){
                    window.location.reload(true);
                }else{
                    $current_demo_URL = window.location.href;
                    $new_demo_URL = $current_demo_URL.replace($old_demo_id, $new_demo_id);
                    window.location.replace($new_demo_URL);
                }
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
        state: {
            required: true
        },
        editorsdemoid: {
            required: true
        },
    },
    messages: {

        title: {
            required: "please fill title field",
            minlength: "Your title must be at least 5 characters"
        },
        state: {
            required: "please fill  state"
        },
        editorsdemoid: {
            required: "please fill  editorsdemoid"
        },
    },
    submitHandler: function() {
        console.log("validated ok submitDemoformAJAX");
        // your ajax loading logic
        // form.submit(); // use this to finally submit form data at the last step
        submitDemoformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});

// Execute save DDL procedure in case of shortcut activation
$editor.commands.addCommand({
    name: 'save',
    bindKey: { win: "Ctrl-S", "mac": "Cmd-S" },
    exec: saveDDL
});

// Save DDL in case of changes
function saveDDL() {
    if (last_DDL_saved.localeCompare($editor.getValue()) != 0) submitDDL('/cp/ajax_save_demoinfo_ddl/')
}

// Prevent redirect if there are changes in the editor
$(window).bind('beforeunload', function (e) {
    if (last_DDL_saved.localeCompare($editor.getValue()) != 0) return 'Are you sure you want to leave?';
});