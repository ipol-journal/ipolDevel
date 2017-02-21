/**
 * @file 
 * this file contains the code that runs de demo
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";


// ipol application namespace
var ipol = ipol || {};


//------------------------------------------------------------------------------
/**
 * ipol.RunDemo interface
 * @constructor
 * @param {object} ddl_json Demo description object (DDL)
 * @param {string} input_origin 
 * @param {object} crop_info crop information in case of crop 
 * @param {object} blobset selected blobset if any (or undefined)
 * @param {object} feature drawing instance of DrawBase class:
 * can be any class Drawing feature class: DrawMask, DrawLines, etc... 
 * or undefined
 */

ipol.RunDemo = function(ddl_json,input_origin, crop_info, blobset, drawfeature) {

    /** 
     * By convention, we create a private variable '_this' to
     * make the object available to the private methods.
     * @var {object} _this
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _this = this;
    
    /** 
     * The Demo Description Lines (DDL) object.
     * @var {object} _ddl_json
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _ddl_json      = ddl_json;
    
    /** 
     * The Demo Description Lines (DDL) object.
     * @var {object} _input_origin
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _input_origin = input_origin;
    
    /** 
     * Contains the crop information: {enabled, x, y, w, h}.
     * @var {object} _crop_info
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _crop_info = crop_info;
    
     /**
      * Define blobset variable.
      * @memberOf ipol.RunDemo~
      * @var {object} _blobset contains information about the selected blobset
      * @defaults undefined
      * @private
      */
    var _blobset = blobset;
    
     /**
      * feature drawing class instance.
      * @memberOf ipol.RunDemo~
      * @var {object} _drawfeature DrawBase instance
      * @private
      */
    var _drawfeature = drawfeature;
    
    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} _verbose
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _verbose=true;

    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function _infoMessage
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ipol.RunDemo ----");
            console.info.apply(console,args);
        }
    }

    //--------------------------------------------------------------------------
    /**
     * Displays message in console independently of verbose 
     * @function _priorityMessage
     * @memberOf ipol.RunDemo~
     * @private
     */
    var _priorityMessage = function( ) {
        var args = [].slice.call( arguments ); //Convert to array
        args.unshift("---- ipol.RunDemo ----");
        console.info.apply(console,args);
    }

    //--------------------------------------------------------------------------
    /**
     * converts the object to a string that can be used in url params
     * @function _json2Uri
     * @memberOf ipol.RunDemo~
     * @param {object} json
     * @private
     * @returns {string}
     */
    var _json2Uri = function(json) {
            return encodeURIComponent(JSON.stringify(json));
    }


    //--------------------------------------------------------------------------
    /**
     * Gets the upload window state for browser history events. Uploaded file
     * are stored in $('#localdata_preview_'+idx).data("src_pos")
     * @function _getUploadPageState
     * @memberOf ipol.RunDemo~
     * @returns {object} upload state object containing, for each input
     * index, the associated src_pos.
     * @private
     */
    var _getUploadPageState = function() {
        var upload_state = {};
        var inputs  = _ddl_json.inputs;
        for(var idx=0;idx<inputs.length;idx++) {
            upload_state[idx] =  $('#localdata_preview_'+idx).data("src_pos");
        }
        return upload_state;
    }

    
    //--------------------------------------------------------------------------
    /**
     * Display results and anything needed after a demo run
     * @function _onDemoRun
     * @memberOf ipol.RunDemo~
     * @param {object} res result obtained from running the demo
     * @private
     * @fires archive:add_experiment
     * @fires History.pushState
     */
    var _onDemoRun = function(run_demo_res) {
        _priorityMessage("MIGUEL | run_demo_res =", run_demo_res);

        if ((run_demo_res.status==="KO")&&
            (!_ddl_json.general['show_results_on_error'])) {
                _priorityMessage("MIGUEL | get out");
                return;
        }
        _priorityMessage("run_demo run_demo_res=", run_demo_res);
        
        _priorityMessage("MIGUEL | P2");

        // push history state will trigger result drawing ...
        // Set url state for browser history
        var new_state={
            demo_id       : _ddl_json.demo_id,
            state         : 2,
            res           : run_demo_res,
            ddl_json      : _ddl_json,
            scrolltop     : $(window).scrollTop(),
            crop_checked  : $("#id_cropinput").is(':checked')
        };
        // add blobset info if input if from the proposed blobsets
        if (_blobset) {
            new_state["blobset"]      = _blobset;
        } else {
            new_state["upload_state"] = _getUploadPageState();
        }
        
        if (_drawfeature) {
            var di = $("#DrawInputs").data("draw_inputs");
            new_state["feature_state"] = di.getDrawFeature().getState();
        }
        
        try {
            // change url hash
            History.pushState(
                new_state,
                "IPOL Journal - "+_ddl_json.general.demo_title,
                //"IPOLDemos "+_ddl_json.demo_id+" results",
                "?id="+_ddl_json.demo_id+"&res="+_json2Uri(run_demo_res));
        } catch(err) {
            _priorityMessage("error:", err.message);
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Uploads the form that contains the input blobs and runs the demo
     * @function _sendRunForm
     * @memberOf ipol.RunDemo~
     * @param {object} form_data contains the data to send/upload
     * @private
     * @fires core:run 
     */
    var _sendRunForm = function(form_data) {
        // Send form to run method in core
        var path = "/api/core/run";
        
        $('#processingCircle').show();
        
        $('#execStatus').css('color', 'blue');
        $("#execStatus").text("Running algorithm...");
        
        $.ajax(path,
        {
            method: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            //Do not cache the page
            cache: false,
            success: function (res) {
                $('#processingCircle').hide();
                
                if (res.status==="OK") {
                    $('#execStatus').css('color', 'green');
                    $("#execStatus").text("Execution successful");
                }
                else {
                    $('#execStatus').css('color', 'red');
                    $("#execStatus").text("Execution failed: " + res.error);
                }
                
                _infoMessage('POST success; res=',res);
                _onDemoRun(res);
            },
            error: function (res) {
                $('#processingCircle').hide();
                $('#execStatus').css('color', 'red');
                $("#execStatus").text("POST to IPOL run with the API failed");
                _infoMessage('POST error; res=',res);
            }
        });
    };
    
    //--------------------------------------------------------------------------
    /**
     * Sets the 'run' button click event, to call demorunner_old for upload,
     * select blobset with crop or initialize without inputs
     * fill a FormData() variable with all the required information
     * to be able to run the demo in all the cases (blobset selection,
     * local file upload, no inputs, mask drawing, etc...)
     * a parameter input_type is send in the form to inform the run service
     * about the type of input, it can be:
     *  - blobset
     *  - upload
     *  - noinputs
     * @function setRunEvent
     * @memberOf ipol.RunDemo~
     * @public 
     */
    this.setRunEvent = function() {
        $( "#run_button" ).unbind("click").prop("disabled",false);
        $( "#run_button" ).click(
        function(){
            // fill form data to upload
            var form_data = new FormData();
            form_data.append("demo_id",         _ddl_json.demo_id);
            form_data.append("original",        _input_origin==="localfiles");

            // create parameters
            if (_ddl_json.params) {
                var params = ipol.DrawParams.staticGetParamValues(_ddl_json.params);
            } else {
                var params = {};
            }
            
            // add crop info as parameters (would only need image size...)
            if (_crop_info) {
                params['x0']=Math.round(_crop_info.x);
                params['x1']=Math.round(_crop_info.x+_crop_info.w);
                params['y0']=Math.round(_crop_info.y);
                params['y1']=Math.round(_crop_info.y+_crop_info.h);
            }

            if (_drawfeature) {
                _drawfeature.AddToParameters(params);
            }
            
            form_data.append("params",  JSON.stringify(params));
                                 
            // select input from blobset or upload from local files
            _infoMessage("input_origin = ", _input_origin);
            
            var submitted_feature = false;
            if (_drawfeature && _drawfeature.submitDrawing) {
                form_data.append("input_type","upload");
                submitted_feature = _drawfeature.submitDrawing( _ddl_json,
                                                                form_data,
                                                                _sendRunForm);
            }

            if (!submitted_feature) {
                switch (_input_origin) {
                    case "blobset":
                        // Set inputs using blobset
                        // crop at the same time
                        form_data.append( "crop_info",
                                JSON.stringify(_crop_info));
                        form_data.append( "blobs",
                                JSON.stringify(_blobset[0].form_params));
                        form_data.append("input_type","blobset");
                        _sendRunForm(form_data);
                        break;

                    case "localfiles":
                        form_data.append("input_type","upload");

                        var inputs  = _ddl_json.inputs;
                        if (inputs.length===1) {
                            // Upload cropped image to server if the browser
                            // supports `HTMLCanvasElement.toBlob`
                            var crop_enabled = $("#id_cropinput").is(':checked');
                            if (crop_enabled) {
                                var cropped_canvas = $("#localdata_preview_0").cropper('getCroppedCanvas');
                                cropped_canvas.toBlob(
                                    function(blob) {
                                        console.info('adding blob (cropped) : ', blob);
                                        form_data.append('file_0', blob);
                                        form_data.append( "crop_info",JSON.stringify(_crop_info));
                                        _sendRunForm(form_data);
                                    }, 'image/png' );
                            } else {
                                var image_src = $("#original_media_0").attr('src');
                                var base64str = image_src.split(',')[1];
                                var content_type = image_src.split('data:')[1].split(';base64')[0];
                                var binary = atob(base64str.replace(/\s/g, ''));
                                var len = binary.length;
                                var buffer = new ArrayBuffer(len);
                                var view = new Uint8Array(buffer);
                                for (var i = 0; i < len; i++) {
                                    view[i] = binary.charCodeAt(i);
                                }
                                var blob = new Blob( [view], { type: content_type });
                                form_data.append('file_0', blob);
                                _sendRunForm(form_data);
                            }
                        } else {
                            // if several input image, TODO: deal with crop of first image
                            var blobs_in_form=0;
                            var image_src = [];
                            var nb_uploads = 0;
                            for(var idx=0;idx<inputs.length;idx++) {
                                var src = $('#original_media_'+idx).attr("src");
                                // TODO: if image is not optional and src is undefined
                                // send error
                                if (src) {
                                    image_src[idx] = src;
                                    nb_uploads++;
                                }
                            }
                            
                            for(var idx=0;idx<inputs.length;idx++) {
                                if (image_src[idx]) {
                                    image_src[idx]
    //                                var image_src = $("#original_media_0").attr('src');
                                    var base64str = image_src[idx].split(',')[1];
                                    var content_type = image_src[idx].split('data:')[1].split(';base64')[0];
                                    var binary = atob(base64str.replace(/\s/g, ''));
                                    var len = binary.length;
                                    var buffer = new ArrayBuffer(len);
                                    var view = new Uint8Array(buffer);
                                    for (var i = 0; i < len; i++) {
                                        view[i] = binary.charCodeAt(i);
                                    }
                                    var blob = new Blob( [view], { type: content_type });
                                    form_data.append('file_'+idx, blob);
                                    blobs_in_form++;
                                    console.info('blobs_in_form=',blobs_in_form);
                                    if(blobs_in_form==nb_uploads) {
                                        _sendRunForm(form_data);
                                    }
                                }
                            }
                        }
                        break;
                        
                    case "noinputs":
                        form_data.append("input_type","noinputs");
                        _sendRunForm(form_data);
                        break;
                } // end switch input_origin
            } // end if (!submitted_feature)
        }
        );
    }
    
};
