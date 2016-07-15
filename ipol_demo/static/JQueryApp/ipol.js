/**
 * @file this file contains the documentReady() function,
  and deals with the initial interactions of the main page: enable page tabulations,
  set events for several buttons, set events for input description and parameters
  description modal windows, for upload modal window, set event for browser history,
  list available demos and create the demo selection. It deals with
  the demo selection in the function 'Input-Controller'. It calls methods or classes
  from other files to display the demo page: input blobs, descriptions, parameters,
  archive information. 
  The demo can be selected
  from three different inputs (demo_origin enumeration): user widget selection,
  url or browser history. The function 'Set-Archive-Experiment' sets the demo
  page information based on an archive experiment, it is called if the url parameters
  contain an experiment id together with the demo id.
 * @author  Karl Krissian
 * @version 0.1
 */

// using strict mode: better compatibility
"use strict";

/**
 * Image Processing OnLine (IPOL) journal demo system namespace
 * @namespace
 */
var ipol = ipol || {};


//------------------------------------------------------------------------------
/**
 *    preprocess DDL demo, filling some properties:
 *        input.max_pixels if string
 *        input.max_weight if string
 *    default values for:
 *        general.crop_maxsize
 *        general.thumbnail_size
 *    set array of strings if single string for
 *        general.input_description
 *        general.param_description
 *    default value for 
 *        params_layout
 * @param {object} demo
 */
ipol.preprocessDemo = function(demo) {
    //
//     console.info("preprocessDemo")
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
                ["Parameters:", ipol.utils.range(demo.params.length)]
            ];
        }
    }
};

//------------------------------------------------------------------------------
/**
 * Get the url parameters
 * @returns {object} containing the name and values of the parameters
 */
ipol.getUrlParameters = function() {
    
    var url_params = {};
    location.search.substr(1).split("&").forEach(function(item) {
        var s = item.split("="),
            k = s[0],
            v = s[1] && decodeURIComponent(s[1]);
        (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
    });
    return url_params;
}

//------------------------------------------------------------------------------
/**
 * Function called when the demo list is received
 * @param {object} demolist returned by the demoinfo module
 */
ipol.onDemoInfoDemoList = function(demolist)
{
    //--------------------------------------------------------------------------
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- onDemoInfoDemoList ----");
            console.info.apply(console,args);
        }
    }
    this.verbose=false;
    
    var dl = demolist;
    if (dl.status == "OK") {
        this.InfoMessage("demo list is ",dl);
    }

    // Get the URL parameters
    var url_params = ipol.getUrlParameters();
    this.InfoMessage("url parameters = ",url_params);
    // Check for 'id' parameter
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
        ipol.setDemoPage(dl.demo_list[demo_pos].editorsdemoid,
                        dl.demo_list[demo_pos].id,
                        ipol.demo_origin.url
                    );
    }

    $("#demo-select").data("demo_list",dl.demo_list);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            ipol.setDemoPage(dl.demo_list[pos].editorsdemoid,
                        dl.demo_list[pos].id,
                        ipol.demo_origin.select_widget
                        );
        });
};

//------------------------------------------------------------------------------
/**
 * List all demos and select one
 */
ipol.listDemos = function (){
//     console.info("get demo list from server");
    ipol.utils.ModuleService(
        'demoinfo',
        'demo_list',
        '',
        ipol.onDemoInfoDemoList
    );
};

/**
 * Enum for demo origin
 * @readonly
 * @enum {number}
 */
ipol.demo_origin =  {  
    /** demo selected from the webpage selector */
    select_widget:0, 
    /** demo specified in the url parameters */
    url:1, 
    /** demo obtained from using the browser history features */
    browser_history:2
};


//------------------------------------------------------------------------------
/**
 * set the demo page based on the archive experiment information
 * @param {object} ddl_json demo description (DDL)
 * @param {object} experiment contains the experiment files and results
 */
ipol.setArchiveExperiment = function (ddl_json, experiment) {
    
    // do as if data is being uploaded
    // fill upload areas with image sources
    // look for input files 
    var archive_input_description = [];
    var archive_input_url         = [];
    var found_inputs=0;
    var nb_inputs = ddl_json.inputs.length;
    
    for(var i=0;i<nb_inputs;i++) {
        // check input_XX.ext
        // check filename to look for in archive description
        var filename = "input_"+i+ddl_json.inputs[i].ext;
        archive_input_url[i] = ipol.ArchiveDisplay.staticFindArchiveUrl(
            filename, ddl_json.archive.files, experiment.files);
        // check input_XX.orig.ext
        if (!archive_input_url[i]) {
            // check filename to look for in archive description
            var filename = "input_"+i+'.orig.png';
            archive_input_url[i] = ipol.ArchiveDisplay.staticFindArchiveUrl(
                filename, ddl_json.archive.files, experiment.files);
        }
        // check input_XX.sel.ext
        // TODO: if we choose .sel then the possible crop is already applied ...
        if (!archive_input_url[i]) {
            // check filename to look for in archive description
            var filename = "input_"+i+'.sel.png';
            archive_input_url[i] = ipol.ArchiveDisplay.staticFindArchiveUrl(
                filename, ddl_json.archive.files, experiment.files);
        }
        if (archive_input_url[i]||(ddl_json.inputs[i].required===false)) {
            // count it as found this it is not required
            found_inputs++;
        }
    }
    
    // on everything loaded, set the inputs
    function SetInputs() {
        var di = new ipol.DrawInputs(ddl_json);
        console.info("apply_local_data ", ddl_json);
        di.setBlobSet(null);
        di.createHTML();
        di.loadDataFromLocalFiles();
        var run = new ipol.RunDemo(ddl_json,
                                   di.getInputOrigin(),
                                   di.getCropInfo(),
                                   di.getBlobSet(), di.getInpaint() );
        run.setRunEvent();
    }
    
    if (found_inputs==nb_inputs) {
        var total_loaded_images = 0;
        // set uploaded files
        for(var i=0;i<nb_inputs;i++) {
            if (archive_input_url[i]) {
                var im = new Image();
                im.crossOrigin = "Anonymous";
                im.onload = function() { 
                    total_loaded_images++;
                    if (total_loaded_images==nb_inputs) {
                        SetInputs();
                    }
                };
                im.src = archive_input_url[i];
                $('#localdata_preview_'+i).attr("src", im.src);
            } else {
                // optional inputs, counted as loaded
                total_loaded_images++;
                if (total_loaded_images==nb_inputs) {
                    SetInputs();
                }
            }
        }
    }
        
    // Set parameter values
    ipol.DrawParams.staticSetParamValues(experiment.results.params);
    
    // Set Progress information
    ipol.RunDemo.staticSetProgress(experiment.results);
    // Draw results
    var dr = new ipol.DrawResults( experiment.results, ddl_json.results );
    // Telling the DrawResults object that we are drawing results from 
    // an experiment so it can search the urls from archive
    dr.setExperiment(experiment,ddl_json.archive);
    dr.create();
}

//------------------------------------------------------------------------------
/**
 * Starts everything needed for demo input tab.
 * @param {number} demo_id the demo id
 * @param {number} internal_demoid the internal demo id for demoinfo module
 * @param {ipol.demo_origin} origin of enum type demo_origin
 * @param {callback} func
 * @fires demoinfo:read_last_demodescription_from_demo
 * @fires blobs:get_blobs_of_demo_by_name_ws
 * @fires archive:get_experiment
 */
ipol.setDemoPage = function (demo_id,internal_demoid,origin,func) {
    
    if (origin===undefined) {
        origin=ipol.demo_origin.select_widget;
    }

    // console.info("internal demo id = ", internal_demoid);
    if (internal_demoid > 0) {
        ipol.utils.ModuleService(
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
                    var ddl_json = ipol.utils.DeserializeJSON(demo_ddl.last_demodescription.json);
                    var str = JSON.stringify(ddl_json, undefined, 4);
                    $("#tabs-ddl pre").html(ipol.utils.syntaxHighlight(str));
                } else {
                    console.error(" --- failed to read DDL");
                }
                
                // update document title
                //$(document).attr("title","IPOL Journal &middot; "+ddl_json.general.demo_title);
                $('title').html("IPOL Journal &middot; "+ddl_json.general.demo_title);

                // for convenience, add demo_id field to the json DDL 
                ddl_json['demo_id'] = demo_id
                ipol.preprocessDemo(ddl_json);
                
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
                    $( "#run_button" ).unbind("click").prop("disabled",true);
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
                        $("#InputDescription").html(ipol.utils.joinHtml(ddl_json.general.input_description));
                        $("#description_input").show();
                    } else {
                        $("#description_input").hide();
                    }
                    // Create local data selection to upload 
                    ipol.upload.ManageLocalData(ddl_json);

                } else {
                    $( "#run_button" ).unbind("click").prop("disabled",true);
                    $(".progress-label").text( "Run" );
                    $("#selectinputs_fieldset").hide();
                    $("#inputs_fieldset"      ).hide();

                    var di = new ipol.DrawInputs(ddl_json);
                    di.setInputOrigin("noinputs");
                    var run = new ipol.RunDemo(ddl_json,
                                               di.getInputOrigin(),
                                               di.getCropInfo(),
                                               di.getBlobSet(), di.getInpaint() );
                    run.setRunEvent();
                }
                
                // Create Parameters tab
                var params = new ipol.DrawParams();
                params.createParams(ddl_json);

                // Get demo blobs
                ipol.utils.ModuleService(
                    "blobs",
                    "get_blobs_of_demo_by_name_ws",
                    "demo_name=" + demo_id,
                    ipol.DrawBlobs.staticOnDemoBlobs(ddl_json));
                
                // Display archive information
                var ar = new ipol.ArchiveDisplay();
                // get and display the last archive page
                ar.getArchive(demo_id,-1);

                if (demo_ddl.status == "OK") {
                    switch(origin) {
                        // user selection from the widget
                        case ipol.demo_origin.select_widget:
                            // !from_url mean the event is from changing the demo id
                            try {
                                // change url hash
                                History.pushState({demo_id:demo_id,state:1}, 
                                "IPOL Journal - "+ddl_json.general.demo_title,
                                //"IPOLDemos "+demo_id+" inputs", 
                                "?id="+demo_id+"&state=1");
                            } catch(err) {
                                console.error("error:", err.message);
                            }
                            break;
                        // demo selection from the url parameters
                        case ipol.demo_origin.url:
                            // check if result to display
                            // Get the URL parameters
                            var url_params = ipol.getUrlParameters();
                            
                            // set results as url parameters
                            if (url_params["res"]!==undefined) {
                                var res = JSON.parse(url_params["res"]);
                                console.info("***** demo results obtained from url parameters");
                                // Set parameter values
                                ipol.DrawParams.staticSetParamValues(res.params);
                                // Set Progress information
                                ipol.RunDemo.staticSetProgress(res);
                                // Draw results
                                var dr = new ipol.DrawResults( res, ddl_json.results );
                                dr.create();
                                //$("#progressbar").get(0).scrollIntoView();
                            }
                            // set experiment id as url parameter
                            if (url_params["exp"]!=undefined) {
                                var exp_id = url_params["exp"][0];
                                console.info("demo experiment = ", exp_id);
                                // ask archive about this experiment
                                var url_params =    'demo_id='    + demo_id + '&id_experiment='+exp_id;
                                ipol.utils.ModuleService("archive","get_experiment",url_params,
                                    function(res) {
                                        console.info("archive get_experiment result : ",res);
                                        if (res['status']==='OK') {
                                            ipol.setArchiveExperiment(ddl_json, res.experiment);
                                        }
                                    }.bind(this));
                            }
                            break;
                        // demo selection from moving in the browser history
                        case ipol.demo_origin.browser_history:
                            if (func!=undefined) {
                                func();
                            }
                            break;
                    }
                }
            });
    }

}
    

//------------------------------------------------------------------------------
/**
 * allow folding/unfolding of legends
 * @param selector
 */
ipol.setLegendFolding = function ( selector) {
    
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
/**
 * Starts processing when document is ready
 */
ipol.documentReady = function () {

    // be sure to have string function endsWith
    if (typeof String.prototype.endsWith !== 'function') {
        String.prototype.endsWith = function(suffix) {
            return this.indexOf(suffix, this.length - suffix.length) !== -1;
        };
    }

    $("#tabs").tabs({
            // update archive tab when selected
            beforeActivate: function(event, ui) {
                if (ui.newPanel.is("#tabs-archive")) {
                    var ar = new ipol.ArchiveDisplay();
                    // we need the demo_id here
                    var demo_list = $("#demo-select").data("demo_list");
                    if (demo_list) {
                        var pos =$( "#demo-select option:selected" ).val();
                        // get and display the last archive page
                        ar.getArchive(demo_list[pos].editorsdemoid,-1);
                    }
                }
            }
        }
    );

    $( "#progressbar" ).progressbar({ value:100 });
    $(".progress-label").text( "Waiting for input selection" );

    ipol.setLegendFolding("legend");
    $("#reset_params").unbind();
    $("#reset_params").click( function() {
        console.info("reset params clicked");
        ipol.DrawParams.staticResetParamValues();
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

    $("#upload-data").button().on("click", 
        function() 
        { 
            dialog.dialog("open");
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
        }
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
    

    ipol.listDemos();

    var History = window.History;
    // Bind to State Change
    History.Adapter.bind(window,'statechange',
        function(p){ // Note: We are using statechange instead of popstate
            console.info(" statechange param:",p);
            console.info("last_uploaded_files:",ipol.upload.last_uploaded_files);
            // Log the State
            var State = History.getState(); 
            // Note: We are using History.getState() instead of event.state
            ipol.history.SetPageState(State.data);
        });

}
$(document).ready(ipol.documentReady);