
// using strict mode: better compatibility
"use strict";



//------------------------------------------------------------------------------
// preprocess DDL demo, filling some properties:
//   input.max_pixels if string
//   input.max_weight if string
// default values for:
//   general.crop_maxsize
//   general.thumbnail_size
// set array of strings if single string for
//   general.input_description
//   general.param_description
// default value for 
//    params_layout
// 
function PreprocessDemo(demo) {
    //
//     console.info("PreprocessDemo")
//     console.info(demo)
    if (demo != undefined) {
        for (var idx=0; idx<demo.inputs.length;idx++) {
            // do some pre-processing
            if ($.type(demo.inputs[idx].max_pixels) === "string") {
                demo.inputs[idx].max_pixels = eval(demo.inputs[idx].max_pixels);
            }
            if ($.type(demo.inputs[idx].max_weight) === "string") {
                demo.inputs[idx].max_weight = eval(demo.inputs[idx].max_weight);
            }
        }
    }
    //

    if (demo.general.crop_maxsize == undefined) {
        // setting the crop_maxsize string to a non integer value with 
        // disable its behavior, so no limit by default
        demo.general.crop_maxsize = "NaN";
    }

    if (demo.general.thumbnail_size == undefined) {
        demo.general.thumbnail_size = 128;
    }

    if ($.type(demo.general.input_description) === "string") {
        demo.general.input_description = [demo.general.input_description];
    }
    if ($.type(demo.general.param_description) === "string") {
        demo.general.param_description = [demo.general.param_description];
    }

    // create default params_layout property if it is not defined
    if (demo.params&&(demo.params_layout == undefined)) {
        if (demo.params!=undefined) {
            demo.params_layout = [
                ["Parameters:", range(demo.params.length)]
            ];
        }
    }
};






//------------------------------------------------------------------------------
function OnDemoList(demolist)
{
    
    //--------------------------------------------------------------------------
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- OnDemoList ----");
            console.info.apply(console,args);
        }
    }
    this.verbose=false;
    
    var dl = demolist;
    if (dl.status == "OK") {
        var str = JSON.stringify(dl.demo_list, undefined, 4);
        $("#tabs-demos pre").html(syntaxHighlight(str))
        this.InfoMessage("demo list is ",dl);
    }


    // get url parameters (found on http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript/21152762#21152762)
    var url_params = {};
    this.InfoMessage("*** OnDemoList location.search=",location.search);
    location.search.substr(1).split("&").forEach(function(item) {
        var s = item.split("="),
            k = s[0],
            v = s[1] && decodeURIComponent(s[1]);
        (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
    })
    this.InfoMessage("url parameters = ",url_params);
    if (url_params["id"]!=undefined) {
        var demo_id = url_params["id"][0];
        this.InfoMessage("demo_id = ", demo_id);
    }
    
    // create a demo selection
    var html_selection = "<select id='demo_selection'>";
    var demo_pos = -1;
    for (var i=0; i<dl.demo_list.length; i++) {
        if (dl.demo_list[i].editorsdemoid==demo_id) {
            this.InfoMessage("found demo id at position ", i);
            demo_pos=i;
        }
        html_selection += '<option value = "'+i+'">'
        html_selection += dl.demo_list[i].editorsdemoid + 
                          '  '+ dl.demo_list[i].title
        
        html_selection += '</option>'
    }
    html_selection += "</select>";
    $("#demo-select").html(html_selection);
    
    if (demo_pos!=-1) {
        $("#demo_selection").val(demo_pos);
        InputController(dl.demo_list[demo_pos].editorsdemoid,
                        dl.demo_list[demo_pos].id,
                        demo_origin.url
                       );
    }

    
    $("#demo-select").data("demo_list",dl.demo_list);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            InputController(dl.demo_list[pos].editorsdemoid,
                            dl.demo_list[pos].id,
                            demo_origin.select_widget
                           );
        });
    

};

//------------------------------------------------------------------------------
// List all demos and select one
//
function ListDemosController() {
    
//     console.info("get demo list from server");
    var dl;

    ModuleService(
        'demoinfo',
        'demo_list',
        '',
        OnDemoList
    );
    
    
};



var demo_origin =  {  select_widget:0, url:1, browser_history:2};

//------------------------------------------------------------------------------
// Starts everything needed for demo input tab
// origin is of enum type demo_origin
//
function InputController(demo_id,internal_demoid,origin,func) {
    
    if (origin===undefined) {
        origin=demo_origin.select_widget;
    }

//     console.info("internal demo id = ", internal_demoid);
    if (internal_demoid > 0) {
        ModuleService(
            'demoinfo',
            'read_last_demodescription_from_demo',
            'demo_id=' + internal_demoid + '&returnjsons=True',
            function(demo_ddl) {
                //console.info("read demo ddl status = ", demo_ddl.status);

                // empty inputs
                $("#DrawInputs").empty();
                $("#DrawInputs").removeData();
                
                // empty results
                $("#ResultsDisplay").empty();
                $("#ResultsDisplay").removeData();
                
                if (demo_ddl.status == "OK") {
                    var ddl_json = DeserializeJSON(demo_ddl.last_demodescription.json);
                    var str = JSON.stringify(ddl_json, undefined, 4);
                    $("#tabs-ddl pre").html(syntaxHighlight(str));
                } else {
                    console.error(" --- failed to read DDL");
                }
                
                // for convenience, add demo_id field to the json DDL 
                ddl_json['demo_id'] = demo_id
                PreprocessDemo(ddl_json);
                
                // hide parameters if none
                if ((ddl_json.params===undefined)||
                    (!(ddl_json.params.length>0))) {
                    $("#parameters_fieldset").hide();
                } else {
                    $("#parameters_fieldset").show();
                }
                //console.info("pd = ",ddl_json.general.param_description);
                if ((ddl_json.general.param_description != undefined) &&
                    (ddl_json.general.param_description != "")&&
                    (ddl_json.general.param_description != [""]))
                {
                    $("#description_params").show();
                } else {
                    $("#description_params").hide();
                }

                var has_inputs = (ddl_json.inputs!==undefined)&&(ddl_json.inputs.length>0);
                if (has_inputs) {
                    // ensure inputs fieldsets are shown 
                    $("#selectinputs_fieldset").show();
                    $("#inputs_fieldset"      ).show();
                    
                    // disable run
                    $( "#progressbar" ).unbind("click");
                    $(".progress-label").text( "Waiting for input selection" );
                    if (ddl_json.general.thumbnail_size!==undefined) {
                        $("#ThumbnailSize").val(ddl_json.general.thumbnail_size);
                    } else {
                        $("#ThumbnailSize").val(128);
                    }
                    if ((ddl_json.general.input_description != undefined) &&
                        (ddl_json.general.input_description != "")&&
                        (ddl_json.general.input_description != [""]))
                    {
                        $("#InputDescription").html(joinHtml(ddl_json.general.input_description));
                        $("#description_input").show();
                    } else {
                        $("#description_input").hide();
                    }
                    // Create local data selection to upload 
                    CreateLocalData(ddl_json);

                } else {
                    $( "#progressbar" ).unbind("click");
                    $(".progress-label").text( "Run" );
                    $("#selectinputs_fieldset").hide();
                    $("#inputs_fieldset"      ).hide();

                    var di = new DrawInputs(ddl_json);
                    di.input_origin = "noinputs";
                    di.SetRunEvent();
                }
                
                // Create Parameters tab
                CreateParams(ddl_json);

                // Get demo blobs
                ModuleService(
                    "blobs",
                    "get_blobs_of_demo_by_name_ws",
                    "demo_name=" + demo_id,
                    OnDemoBlobs(ddl_json));
                
                // Display archive information
                var ar = new ArchiveDisplay();
                ar.get_archive(demo_id,1);

                if (demo_ddl.status == "OK") {
                    switch(origin) {
                        case demo_origin.select_widget:
                            // !from_url mean the event is from changing the demo id
                            try {
                                // change url hash
                                History.pushState({demo_id:demo_id,state:1}, "IPOLDemos "+demo_id+" inputs", "?id="+demo_id+"&state=1");
                            } catch(err) {
                                console.error("error:", err.message);
                            }
                            break;
                        case demo_origin.url:
                            // check if result to display
                            var url_params = {};
                            location.search.substr(1).split("&").forEach(function(item) {
                                var s = item.split("="),
                                    k = s[0],
                                    v = s[1] && decodeURIComponent(s[1]);
                                (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
                            });
                            if (url_params["res"]!==undefined) {
                                var res = JSON.parse(url_params["res"]);
                                console.info("***** demo results obtained from url parameters");
                                // Set parameter values
                                SetParamValues(res.params);
                                // Draw results
                                if ($("#DrawInputs").data("draw_inputs")) {
                                    $("#DrawInputs").data("draw_inputs").ResultProgress(res);
                                }
                                var dr = new DrawResults( res, ddl_json.results );
                                dr.Create();
                                //$("#progressbar").get(0).scrollIntoView();
                            }
                            break;
                        case demo_origin.browser_history:
                            if (func!=undefined) {
                                func();
                            }
                            break;
                    }
                }
                
            });


    }
    

}
    
    
// for browser history features, save last uploaded files locally
var last_uploaded_files = [];
// use windows.localStorage to avoid displaying a wrong input 
// (position will be unique for each upload, even after page refresh)
var last_uploaded_files_pos = window.localStorage.getItem("last_uploaded_files_pos");
if (!last_uploaded_files_pos) {
    last_uploaded_files_pos = 0;
    window.localStorage.setItem("last_uploaded_files_pos", last_uploaded_files_pos);
}
    
//------------------------------------------------------------------------------
// deals with the user blobs to upload
//
function CreateLocalData(ddl_json) {
    var html="";
    html += '<table style="margin-right:auto;margin-left:0px">';
    for(var i=0;i<ddl_json.inputs.length;i++) {
        html += '<tr>';
        html += '<td>';
          html += '<label for="file_'+i+'">'+ddl_json.inputs[i].description+'</label>';
        html += '</td>';
        html += '<td>';
          html += '<input type="file" name="file_'+i+'" id="file_'+i+'" size="40"';
          html += 'accept="'+ddl_json.inputs[i].ext+',image/*,media_type"';
          html += ' />';
        html += '</td>';
        html += '<td > <img id="localdata_preview_'+i+'" style="max-height:128px"></td>';
        html += '<td>';
        html += '<font size="-1"><i>';
          if (ddl_json.inputs[i].max_pixels!=undefined) {
            html += '<span>  &le;'+ddl_json.inputs[i].max_pixels+' pixels </span>';
          }
          if (ddl_json.inputs[i].max_weight!=undefined) {
            html += '<span> &le;'+ddl_json.inputs[i].max_weight/(1024*1024)+' Mb </span>';
          }
          if (ddl_json.inputs[i].required!=undefined && !ddl_json.inputs[i].required) {
            html += '<span> (optional) </span>';
          }
        html += '</i></font>';
        html += '</td>';
        html += '</tr>';
    }
    html += '</table>';
    //html += '<input type="submit" value="select" />';
    $("#local_data").html(html);
    
//     // deal with events
//     $( "#apply_localdata" ).click( (function(ddl_json) { return function(){
//             // code to be executed on click
//             var di = new DrawInputs(ddl_json);
//             console.info("apply_local_data ", ddl_json);
//             di.SetBlobSet(null);
//             di.CreateHTML();
//             //di.CreateCropper();
//             di.LoadDataFromLocalFiles();
//             di.SetRunEvent();
//         }
//     })(ddl_json));
    
    $("#upload-dialog").dialog("option","buttons",{
        Apply: (function(ddl_json) { 
            return function(){
                // code to be executed on click
                var di = new DrawInputs(ddl_json);
                console.info("apply_local_data ", ddl_json);
                di.SetBlobSet(null);
                di.CreateHTML();
                //di.CreateCropper();
                di.LoadDataFromLocalFiles();
                di.SetRunEvent();
                $(this).dialog( "close" );
            }
        })(ddl_json),
        Cancel: function() {
          $(this).dialog( "close" );
        }
      });
    
    
    for(var i=0;i<ddl_json.inputs.length;i++) {
        $("#file_"+i).change( 
            (function(i) { return function() {

                console.info("files=",this.files);
                var size_ok = this.files[0].size<eval(ddl_json.inputs[i].max_weight);
                var Mb=1024*1024;
                var file_size     = this.files[0].size/Mb;
                var allowed_size  = eval(ddl_json.inputs[i].max_weight)/Mb;
                console.info(" size ok = ", file_size.toPrecision(5), "<", 
                             allowed_size.toPrecision(5));
                if (!size_ok) {
                    alert("The selected file exceeds the maximal allowed size: "+ 
                            file_size.toPrecision(4)+" Mb >"+
                            allowed_size.toPrecision(4)+" Mb");
                    return;
                }
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = (function(i) { return function (e) {
                        console.info("onload ", i, ":",e.target);
                        $('#localdata_preview_'+i).attr("src", e.target.result);
                        console.info("size of uploaded file :", e.target.result.length/1024/1024, " Mb" );
                        last_uploaded_files[last_uploaded_files_pos] = e.target.result;
                        $('#localdata_preview_'+i).data("src_pos",last_uploaded_files_pos);
                        last_uploaded_files_pos++;
                        window.localStorage.setItem("last_uploaded_files_pos", last_uploaded_files_pos);
                        // avoid filling the memory by release old files
                        if (last_uploaded_files_pos>=10) {
                            last_uploaded_files[last_uploaded_files_pos-10]=undefined;
                        }
                        
                    } })(i);
                    reader.readAsDataURL(this.files[0]);
                }
            } }) (i)
        );
    }
}
    

//------------------------------------------------------------------------------
// allow folding/unfolding of legends
//
function SetLegendFolding( selector) {
    
    // Set cursor to pointer and add click function
    $(selector).css("cursor","pointer").click(function(){
        var legend = $(this);
        var value = $(this).children("span").html();
        if(value=="[-]")
            value="[+]";
        else
            value="[-]";
       $(this).siblings().slideToggle("slow", function() { legend.children("span").html(value); } );
    });
}    
    
//------------------------------------------------------------------------------
// SetPageState
//
function SetPageState( page_state) {

    //--------------------------------------------------------------------------
    function SetPageDemo(demo_id, onpage_func) {
        if (demo_id===undefined) {
            return;
        }
        var demo_list = $("#demo-select").data("demo_list");
        var demo_position = -1;
        for(var i=0;i<demo_list.length;i++) {
            if (demo_list[i].editorsdemoid==demo_id) {
                demo_position = i;
                break;
            }
        }
        
        if ((demo_position!=-1)&&(demo_position!=$("#demo_selection").val())) {
            console.info("!!! demo id has changed !!! trigger change ", 
                        demo_list[$("#demo_selection").val()].editorsdemoid, ",", 
                        "-->", demo_id);
            $("#demo_selection").val(demo_position);
            // don't trigger change since it will push a new history state,
            // instead, execute the change as if the url was loaded
            // which means we draw parameters and results too
            InputController(demo_list[demo_position].editorsdemoid,
                            demo_list[demo_position].id,
                            demo_origin.browser_history,
                            onpage_func
                        );
        } else {
            onpage_func();
        }
    }
    
    //--------------------------------------------------------------------------
    function SetInputsState(blobset,upload_state, ddl_json,params,crop_checked) {
        var di = $("#DrawInputs").data("draw_inputs");
        var crop_area = {   
            x:      params.x0, 
            y:      params.y0, 
            width:  params.x1-params.x0,
            height: params.y1-params.y0
        };
        console.info("1 di=",di);
        // recreate only if it has changed:
        if ((!di)||(!objectEquals(ddl_json,di.ddl_json))) {
            if (di) { console.info("2", ddl_json, " != ",di.ddl_json); }
            di = new DrawInputs(ddl_json);
            // just in case, be sure nothing is on upload page
            di.UnsetUploadPageState();
        }
        if (blobset) {
            console.info("3");
            if (!objectEquals(blobset,di.GetBlobSet())) {
                console.info("4 ",blobset,' != ', di.GetBlobSet());
                di.SetBlobSet(blobset);
                di.input_origin = "blobset";
                di.UnsetUploadPageState();
                di.CreateHTML();
                $("#id_cropinput").prop('checked',crop_checked);
                di.OnCropBuilt( function() {
                    console.info("OnCropBuilt callback");
                    di.OnCropBuilt( undefined);
                    if (crop_checked) {
                        // does not work yet
                        console.info("crop_area is ", crop_area);
                        di.SetCrop(crop_area);
                    }
                });
                di.OnLoadImages( function() {
                    console.info("OnLoadImages callback");
                });
                di.LoadDataFromBlobSet();
            } else {
                console.info("5");
                // blobset is already loaded, set crop
                if (crop_checked!=$("#id_cropinput").prop('checked')) {
                    if (crop_checked) {
                        // change from crop disabled to crop unabled, start crop
                        di.OnCropBuilt( function() { 
                            di.SetCrop(crop_area); 
                            di.OnCropBuilt(undefined); 
                        });
                    }
                    $("#id_cropinput").prop('checked',crop_checked);
                    console.info('trigger croinput change');
                    $("#id_cropinput").trigger('change'); 
                } else {
                    if (crop_checked) {
                        // does not work yet
                        console.info("crop_area is ", crop_area);
                        di.SetCrop(crop_area);
                    }
                }
            }
            di.SetRunEvent();
        }
        if (upload_state) {
            console.info("10");
            var upload_res = di.SetUploadPageState(upload_state);
            if (upload_res!=1) {
                di.UnsetBlobSet();
                di.input_origin = "localfiles";
                if (upload_res==0) {
                    di.CreateHTML();
                    $("#id_cropinput").prop('checked',crop_checked);
                    di.OnCropBuilt( function() {
                        console.info("OnCropBuilt callback");
                        di.OnCropBuilt( undefined);
                        if (crop_checked) {
                            console.info("crop_area is ", crop_area);
                            di.SetCrop(crop_area);
                        }
                    });
                    di.OnLoadImages( function() {
                        console.info("OnLoadImages callback");
                    });
                    di.LoadDataFromLocalFiles();
                } else {
                    // data alread loaded, setting crop
                    if (crop_checked!=$("#id_cropinput").prop('checked')) {
                        if (crop_checked) {
                            // change from crop disabled to crop unabled, start crop
                            di.OnCropBuilt( function() { 
                                di.SetCrop(crop_area); 
                                di.OnCropBuilt(undefined); 
                            });
                        }
                        $("#id_cropinput").prop('checked',crop_checked);
                        console.info('trigger croinput change');
                        $("#id_cropinput").trigger('change'); 
                    } else {
                        if (crop_checked) {
                            console.info("crop_area is ", crop_area);
                            di.SetCrop(crop_area);
                        }
                    }
                }
                di.SetRunEvent();
            } else {
                $("#DrawInputs").empty();
                $("#DrawInputs").removeData();
            }
        }
    }
    
    //--------------------------------------------------------------------------
    function SetParamsState(params) {
        // update parameters
        SetParamValues(params);
    }
    
    //--------------------------------------------------------------------------
    function SetResultsState(res,ddl_results,scrolltop) {
        // draw results
        // trick to avoid flickering, set big height to
        // keep the scrolling position
        $("#ResultsDisplay").parent().css("height",$(window).height()+"px")
        
        var dr = new DrawResults( res, ddl_results );
        
        dr.onloadall_callback = function() {
            // reset result display height to empty so it is automatic
            $("#ResultsDisplay").parent().css("height","")
            $(window).scrollTop(page_state.scrolltop);
            console.info("onloadall_callback scrolltop=",scrolltop);
            // disable it 
            console.info("dr=",dr);
//             dr.onloadall_callback=undefined;
        }
        dr.Create();
        //$("#progressbar").get(0).scrollIntoView();
    }
    
    //--------------------------------------------------------------------------
    // find position of demo id
    SetPageDemo(page_state.demo_id,
        function() {
            History.log('statechange:', page_state);
            switch (page_state.state) {
                // state 2: after run execution
                case 2:
                    
                    SetInputsState( page_state.blobset,
                                    page_state.upload_state,
                                    page_state.ddl_json,
                                    page_state.res.params,
                                    page_state.crop_checked
                                );
                    
                    // update parameters
                    SetParamsState(page_state.res.params);
                    
                    var di = $("#DrawInputs").data("draw_inputs");
                    if (di) {
                        di.ResultProgress(page_state.res);
                    }
                    
                    SetResultsState(page_state.res,
                                    page_state.ddl_json.results,
                                    page_state.scrolltop);
                    break;
                // state 1: after demo selection
                case 1:
                default:
                    // empty draw inputs since we don't redraw them for the moment
                    $("#DrawInputs").empty();
                    $("#DrawInputs").removeData();
                    // empty result area
                    $("#ResultsDisplay").empty();
            }
        }
    );
    
    
    
}
    

    
//------------------------------------------------------------------------------
// Starts processing when document is ready
//

function DocumentReady() {
    
//     console.info($(window).width());
//     console.info($(document).width()); 
//     console.info(window.screen.width);
    
    // be sure to have string function endsWith
    if (typeof String.prototype.endsWith !== 'function') {
        String.prototype.endsWith = function(suffix) {
            return this.indexOf(suffix, this.length - suffix.length) !== -1;
        };
    }

    $("#tabs").tabs({
            activate: function(event, ui) {
                var active = $('#tabs').tabs('option', 'active');
            }
        }

    );

    $( "#progressbar" ).progressbar({ value:100 });
    $(".progress-label").text( "Waiting for input selection" );

    SetLegendFolding("legend");
    $("#reset_params").unbind();
    $("#reset_params").click( function() {
        console.info("reset params clicked");
        ResetParamValues();
    }
    );
    
    // parameters description dialog
    var param_desc_dialog;
    param_desc_dialog = $("#ParamDescription").dialog({
        autoOpen: false,
        // height: 500,
        width: 800,
        modal: true,
    });
    
    $("#description_params").button().on("click", 
        function() 
        { 
            param_desc_dialog.dialog("open");
        });

    // input description dialog
    var input_desc_dialog;
    input_desc_dialog = $("#InputDescription").dialog({
        autoOpen: false,
        // height: 500,
        width: 800,
        modal: true,
    });
    
    $("#description_input").button().on("click", 
        function() 
        { 
            input_desc_dialog.dialog("open");
        });

    // upload modal dialog
    var dialog;
    dialog = $("#upload-dialog").dialog({
        autoOpen: false,
        height: 500,
        width: 800,
        modal: true,
        buttons: {
            Cancel: function() {
            dialog.dialog( "close" );
            }
        },
//         close: function(event, ui) {
//             $(this).empty().dialog('destroy');
//         }
    });
    
    // adjusting width of display blobs div
    var displayblobs_parent = $("#displayblobs").parent();
    var to_deduce = displayblobs_parent.outerWidth(true)-displayblobs_parent.width();
    $("#displayblobs").width($("#tabs-run").width()-to_deduce);
    
    $( window ).resize(function() {
        var displayblobs_parent = $("#displayblobs").parent();
        var to_deduce = displayblobs_parent.outerWidth(true)-displayblobs_parent.width();
        $("#displayblobs").width($("#tabs-run").width()-to_deduce);
    }
    );
    
    $("#upload-data").button().on("click", 
        function() 
        { 
            dialog.dialog("open");
        });

    ListDemosController();

    var History = window.History;
    // Bind to State Change
    History.Adapter.bind(window,'statechange',
        function(p){ // Note: We are using statechange instead of popstate
            console.info(" statechange param:",p);
            console.info("last_uploaded_files:",last_uploaded_files);
            // Log the State
            var State = History.getState(); 
            // Note: We are using History.getState() instead of event.state
            SetPageState(State.data);
        });

}
$(document).ready(DocumentReady);