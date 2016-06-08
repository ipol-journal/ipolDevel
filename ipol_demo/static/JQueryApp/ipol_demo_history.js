//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_history.js
// date: june 2016
// author: Karl Krissian
//
// description:
// deal with browser history, move back and forward, etc...
//

// using strict mode: better compatibility
"use strict";


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
    
