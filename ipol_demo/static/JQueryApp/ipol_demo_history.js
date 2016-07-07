/**
 * @file 
 * deal with browser history, move back and forward, etc...
 * @author  Karl Krissian
 * @version 0.1
 */

// using strict mode: better compatibility
"use strict";

// ipol application namespace
var ipol = ipol || {};


/**
 * history
 * @namespace
 */
ipol.history = ipol.history || {};

//------------------------------------------------------------------------------
/**
 * Set page contents based on its state (obtained from browser history)
 * @constructor
 * @param {object} page_state
 */
ipol.history.SetPageState = function( page_state) {

    //--------------------------------------------------------------------------
    /**
     * Set the demo id: changes the selection and the page contents accordingly
     * @param demo_id     {number}
     * @param onpage_func {callback}
     * @function SetPageDemo
     * @memberOf ipol.history.SetPageState~
     */
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
            ipol.setDemoPage(demo_list[demo_position].editorsdemoid,
                        demo_list[demo_position].id,
                        demo_origin.browser_history,
                        onpage_func
                        );
        } else {
            onpage_func();
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Set the demo inputs
     * @param blobset       {object}  blob set to display (can be undefined)
     * @param upload_state  {object}  upload state (can be undefined)
     * @param ddl_json      {object}  DDL object 
     * @param params        {object}  algorithm parameters
     * @param crop_checked  {boolean} if crop is checked
     * @function SetInputsState
     * @memberOf ipol.history.SetPageState~
     */
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
        if ((!di)||(!ipol.utils.objectEquals(ddl_json,di.ddl_json))) {
            if (di) { console.info("2", ddl_json, " != ",di.ddl_json); }
            di = new ipol.DrawInputs(ddl_json);
            // just in case, be sure nothing is on upload page
            di.unsetUploadPageState();
        }
        if (blobset) {
            console.info("3");
            if (!ipol.utils.objectEquals(blobset,di.getBlobSet())) {
                console.info("4 ",blobset,' != ', di.getBlobSet());
                di.setBlobSet(blobset);
                di.setInputOrigin("blobset");
                di.unsetUploadPageState();
                di.createHTML();
                $("#id_cropinput").prop('checked',crop_checked);
                di.onCropBuilt( function() {
                    console.info("OnCropBuilt callback");
                    di.onCropBuilt( undefined);
                    if (crop_checked) {
                        // does not work yet
                        console.info("crop_area is ", crop_area);
                        di.setCrop(crop_area);
                    }
                });
                di.onLoadImages( function() {
                    console.info("OnLoadImages callback");
                });
                di.loadDataFromBlobSet();
            } else {
                console.info("5");
                // blobset is already loaded, set crop
                if (crop_checked!=$("#id_cropinput").prop('checked')) {
                    if (crop_checked) {
                        // change from crop disabled to crop unabled, start crop
                        di.onCropBuilt( function() { 
                            di.setCrop(crop_area); 
                            di.onCropBuilt(undefined); 
                        });
                    }
                    $("#id_cropinput").prop('checked',crop_checked);
                    console.info('trigger croinput change');
                    $("#id_cropinput").trigger('change'); 
                } else {
                    if (crop_checked) {
                        // does not work yet
                        console.info("crop_area is ", crop_area);
                        di.setCrop(crop_area);
                    }
                }
            }
            var run = new ipol.RunDemo(ddl_json,
                                       di.getInputOrigin(),
                                       di.getCropInfo(),
                                       di.getBlobSet(), di.getInpaint() );
            run.setRunEvent();
        }
        if (upload_state) {
            console.info("10");
            var upload_res = di.setUploadPageState(upload_state);
            if (upload_res!=1) {
                di.unsetBlobSet();
                di.setInputOrigin("localfiles");
                if (upload_res==0) {
                    di.createHTML();
                    $("#id_cropinput").prop('checked',crop_checked);
                    di.onCropBuilt( function() {
                        console.info("OnCropBuilt callback");
                        di.onCropBuilt( undefined);
                        if (crop_checked) {
                            console.info("crop_area is ", crop_area);
                            di.setCrop(crop_area);
                        }
                    });
                    di.onLoadImages( function() {
                        console.info("OnLoadImages callback");
                    });
                    di.loadDataFromLocalFiles();
                } else {
                    // data alread loaded, setting crop
                    if (crop_checked!=$("#id_cropinput").prop('checked')) {
                        if (crop_checked) {
                            // change from crop disabled to crop unabled, start crop
                            di.onCropBuilt( function() { 
                                di.setCrop(crop_area); 
                                di.onCropBuilt(undefined); 
                            });
                        }
                        $("#id_cropinput").prop('checked',crop_checked);
                        console.info('trigger croinput change');
                        $("#id_cropinput").trigger('change'); 
                    } else {
                        if (crop_checked) {
                            console.info("crop_area is ", crop_area);
                            di.setCrop(crop_area);
                        }
                    }
                }
                var run = new ipol.RunDemo(ddl_json,
                                           di.getInputOrigin(),
                                           di.getCropInfo(),
                                           di.getBlobSet(), di.getInpaint() );
                run.setRunEvent();
            } else {
                $("#DrawInputs").empty();
                $("#DrawInputs").removeData();
            }
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Set the parameters values
     * @param params        {object}  algorithm parameters
     * @function SetParamsState
     * @memberOf ipol.history.SetPageState~
     */
    function SetParamsState(params) {
        // update parameters
        ipol.params.SetParamValues(params);
    }
    
    //--------------------------------------------------------------------------
    /**
     * Displays the results
     * @param res         {object}  result object
     * @param ddl_results {object}  results section of the DDL
     * @param scrolltop   {number}  scrolling position
     * @function SetResultsState
     * @memberOf ipol.history.SetPageState~
     */
    function SetResultsState(res,ddl_results,scrolltop) {
        // draw results
        // trick to avoid flickering, set big height to
        // keep the scrolling position
        $("#ResultsDisplay").parent().css("height",$(window).height()+"px")
        
        var dr = new ipol.DrawResults( res, ddl_results );
        
        dr.onloadall_callback = function() {
            // reset result display height to empty so it is automatic
            $("#ResultsDisplay").parent().css("height","")
            $(window).scrollTop(scrolltop);
            console.info("onloadall_callback scrolltop=",scrolltop);
            // disable it 
            console.info("dr=",dr);
//             dr.onloadall_callback=undefined;
        }
        dr.create();
        //$("#progressbar").get(0).scrollIntoView();
    }
    
    //--------------------------------------------------------------------------
    // calling SetPageDemo with a callback
    SetPageDemo(page_state.demo_id,
        function() {
            History.log('statechange:', page_state);
            switch (page_state.state) {
                // state 2: after run execution
                // set all the page information
                case 2:
                    
                    SetInputsState( page_state.blobset,
                                    page_state.upload_state,
                                    page_state.ddl_json,
                                    page_state.res.params,
                                    page_state.crop_checked
                                );
                    
                    // update parameters
                    SetParamsState(page_state.res.params);
                    
                    // Set Progress information
                    ipol.RunDemo.staticSetProgress(page_state.res);
                    
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
    
