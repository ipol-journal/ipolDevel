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
$modal_ddl_msg_div='#createddl_modal_errordiv';
$modal_ddl_id='#createDDLFormModalId';
$modal_ddl_header='div#createDDLModalheader';
$form_ddl_id='#DDLform';
//hidden
$form_ddl_field_demo_id="#DDLform #id_demoid";

//normal
$form_ddl_field_ddljson="#DDLform #id_ddlJSON";
var $ddlform = $($form_ddl_id);

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


/*  show/edit DDL modal  */
function send_get_ddl_request(wsurl,demo_id) {

    if (wsurl === undefined) {
        // wsurl was not passed, just open edit modal
        $($modal_ddl_header).html('<h3>New DDL data</h3>');
        $($modal_ddl_id).modal('show');
    }else{
        // wsurl was passed, get data from ws and open show modal
        console.log("send_get_ddl_request");
        $.ajax({
            type: 'POST',
            url: wsurl,
            dataType: 'json',
            success: function(data) {

                if (data.status=='OK'){
                    //clear modal  error
                    $($modal_ddl_msg_div).html('');

                    //edit/show ddl
                    if (data.last_demodescription){

                        //Load ddl data in form
                        //console.log(data.last_demodescription);
                        $($modal_ddl_header).html('<h3>Edit DDL data</h3>');
                        $($form_ddl_field_demo_id).get(0).value = demo_id;
                        //gets json str (result of retrieving str from db)
                        $($form_ddl_field_ddljson).get(0).value = data.last_demodescription.json;
                        $($modal_ddl_id).modal('show');
                        $ddlform.show();

                    //create ddl, the demo has no ddl
                    }else{

                        //Reset Form
                        $($modal_ddl_header).html('<h3>New DDL data</h3>');
                        $($form_ddl_field_demo_id).get(0).value = demo_id;
                        $($form_ddl_field_ddljson).get(0).value = '';
                        $($modal_ddl_id).modal('show');
                        $ddlform.show();
                    }
                }else{
                    //error, no OK
                    var errorhtml="<p class=\"ststsnok\">DDL not retrieved sucessfully, "+$ws_down+"</p>";
                    $($modal_ddl_msg_div).html(errorhtml);
                }
            },
            error: function(data){
                var errorhtml="<p class=\"ststsnok\">Error getting DDL, "+$ws_down+"</p>";
                $($modal_ddl_msg_div).html(errorhtml);
                $($modal_ddl_id).modal('show');
                $ddlform.hide();
            }
        });
    }
}


/*  submit DDL form  */
function submitDDLformAJAX(){

    console.log("submitDDLformAJAX Submit");
    var csrftoken = getCookie('csrftoken');
    var $serializedData = $ddlform.serialize();
    var $ajaxurl = $ddlform.attr("action");

    $.ajax({
        url: $ajaxurl,
        type: "POST",
        /* dataType: "json",*/
        data: $serializedData,
        success: function(data) {
            console.log("AJAX CALL status: "+data.status);
            if (data.status == "OK") {
                $($modal_ddl_msg_div).html('DDL saved').show();
                $ddlform.hide();
                //no need to reaload, the list shows no ddl info
            }else {

                $ddlform.show();
                $error_msg=find_ws_errors(data);
                var errorhtml="<p class=\"ststsnok\">DDL not saved,ws returned: "+$error_msg+"</p>";
                $($modal_ddl_msg_div).html(errorhtml).show();


            }
        },
        error: function () {
            console.log("ajax error");
            var errorhtml="<p class=\"ststsnok\">Error saving DDL, "+$ws_down+"</p>";
            $($modal_ddl_msg_div).html(errorhtml);
            $($modal_ddl_id).modal('show');
            $ddlform.hide();
        }
    });
}


/*  DDL form validation */
$($form_ddl_id).validate({
    errorClass: "validationerror",//for css
    rules: {
        ddlJSON: {
            required: true,
            minlength: 5
        }
    },
    messages: {

        ddlJSON: {
            required: "please fill ddlJSON field",
            minlength: "Your ddlJSON must be at least 5 characters"
        }
    },
    submitHandler: function() {
        console.log("validated ok submitDDLformAJAX");
        // your ajax loading logic
        // form.submit(); // use this to finally submit form data at the last step
        submitDDLformAJAX();
        return false;  // prevent form submit because you are doing the ajax
    }
});


/*  show/edit Demo modal  */
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
        $($form_demo_field_editor).get(0).value = '';
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

                        $($modal_demo_header).html('<h3>Edit Demo data</h3>');
                        /*  $($form_ddl_field_demo_id).get(0).value = demo_id;*/
                        /*  $($form_ddl_field_ddl_id).get(0).value = data.last_demodescription.id;*/
                        /*  $($form_ddl_field_ddljson).get(0).value = $.parseJSON(data.last_demodescription.json);*/
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
                        $($form_demo_field_editor).get(0).value = '';
                        $($modal_demo_id).modal('show');
//                        $demoform.show();
                    }
                }else{
                    //error, no OK
                    console.log(" Error, ws returned KO");

                    $error_msg=find_ws_errors(data);
                    var errorhtml="<p class=\"ststsnok\">Demo not retrieved sucessfully, ws returned "+$error_msg+"</p>";
                    $($modal_demo_id).modal('show');
                    $demoform.hide();
                    $($modal_demo_msg_div).html(errorhtml);
                }
            },
            error: function(data){
                var errorhtml="<p class=\"ststsnok\">Error getting Demo, "+$ws_down+"</p>";
                $($modal_demo_msg_div).html(errorhtml);
                $($modal_demo_id).modal('show');
                $demoform.hide();
            }
        });
    }
}


/*  submit Demo form  */
function submitDemoformAJAX(){

    console.log("submitDemoformAJAX Submit");

    var csrftoken = getCookie('csrftoken');
    var $serializedData = $demoform.serialize();
    var $ajaxurl = $demoform.attr("action");

    console.log($ajaxurl);

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


/*  show pretty json  */
function prettyPrint(formfieldidtopretify) {
    var ugly = document.getElementById(formfieldidtopretify).value;
    var obj = JSON.parse(ugly);
    var pretty = JSON.stringify(obj, undefined, 4);
    document.getElementById(formfieldidtopretify).value = pretty;
}


/*  show ugly json  */
function prettyPrintundo(formfieldidtopretify) {
    var pretty = document.getElementById(formfieldidtopretify).value;
    var obj = JSON.parse(pretty);
    var ugly = JSON.stringify(obj);
    document.getElementById(formfieldidtopretify).value = ugly;
}

