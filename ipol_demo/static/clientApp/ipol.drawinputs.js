/**
 * @file 
 * this file contains the code that renders the selected input blobs
 * including the option to crop the input image
 * associated with ipol_demo.html and ipol_demo.js
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";


// ipol application namespace
var ipol = ipol || {};



//------------------------------------------------------------------------------
/**
 * ipol.DrawInputs interface
 * @constructor
 * @param {object} ddl_json Demo description object (DDL)
 */

ipol.DrawInputs = function(ddl_json) {
    
    /** 
     * By convention, we create a private variable '_this' to
     * make the object available to the private methods.
     * @var {object} _this
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _this = this;

    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function _infoMessage
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ipol.DrawInputs ----");
            console.info.apply(console,args);
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Displays message in console independently of verbose 
     * @function _priorityMessage
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _priorityMessage = function( ) {
        var args = [].slice.call( arguments ); //Convert to array
        args.unshift("---- ipol.DrawInputs ----");
        console.info.apply(console,args);
    }
    
    //--------------------------------------------------------------------------
    // Initialize members
    //--------------------------------------------------------------------------
    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} _verbose
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _verbose=false;
    
    _priorityMessage(" DrawInput started ");
    
    /** 
     * The Demo Description Language DDL object.
     * @var {object} _ddl_json
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _ddl_json      = ddl_json;
    
    /** 
     * Contains image display constraints or information. 
     * For single image display, maxdim is set to 768 so that bigger images
     * will be scaled down. display_ratio is then the calculated display ratio.
     * For multiple images, maxdim will be calculated based on the available 
     * space of the webpage (window).
     * @var {{maxdim: number, display_ratio: number}} _draw_info
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _draw_info     = { maxdim:768,  display_ratio:-1};

    /** 
     * Stores the origin of the inputs, initialized to , it can be 
     * "blobset", "localfiles" or "noinputs" 
     * @var {string} _input_origin
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _input_origin  = "";

    /** 
     * Sets _input_origin private variable
     * @function setInputOrigin
     * @memberOf ipol.DrawInputs~
     * @param {string}
     * @public
     */
    this.setInputOrigin = function(inputorigin) {
        _input_origin = inputorigin;
    }
    
    /** 
     * Gets _input_origin private variable
     * @function getInputOrigin
     * @memberOf ipol.DrawInputs~
     * @returns {string}
     * @public
     */
    this.getInputOrigin = function() {
        return _input_origin;
    }
    
    /** 
     * Contains the crop information: {enabled, x, y, w, h}.
     * @var {object} _crop_info
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _crop_info     = { enabled:false, x:0,y:0,w:1,h:1};
    
    /** 
     * Gets CropInfo private variable
     * @function getCropInfo
     * @memberOf ipol.DrawInputs~
     * @returns {object}
     * @public
     */
    this.getCropInfo = function() {
        return _crop_info;
    }
    

    /** 
     * callback called once crop is built.
     * @var {object} _oncropbuilt_cb
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _oncropbuilt_cb  = undefined;

    /** 
     * callback called once the images are loaded.
     * @var {object} _onloadimages_cb
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _onloadimages_cb = undefined;

    /**
     * Define blobset variable.
     * @memberOf ipol.DrawInputs~
     * @param {object} _blobset contains information about the selected blobset
     * @defaults undefined
     * @private
     */
    var _blobset = undefined;
    
    /** 
     * Gets _blobset private variable
     * @function getBlobSet
     * @memberOf ipol.DrawInputs~
     * @returns {object}
     * @public
     */
    this.getBlobSet = function() {
        return _blobset;
    }
    

    /** 
     * _drawfeature contains the drawing feature 
     * can be drawlines, drawmask, drawpoints, etc.
     * @var {object} _drawfeature
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _drawfeature = undefined;

    // add line drawing features
    if (_ddl_json.general.drawlines) {
        _drawfeature = new ipol.features.DrawLines();
    } else {
        // add point drawing features
        if (_ddl_json.general.drawpoints) {
            _drawfeature = new ipol.features.DrawPoints();
        } else {
            // add drawmask features
            if (_ddl_json.general.drawmask) {
                _drawfeature = new ipol.features.DrawMask();
            }
        }
    }

    /** 
     * Gets _drawfeature private variable
     * @function getDrawFeature
     * @memberOf ipol.DrawInputs~
     * @returns {object}
     * @public
     */
    this.getDrawFeature = function() {
        return _drawfeature;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Undefine blobset variable.
     * @function unsetBlobSet
     * @memberOf ipol.DrawInputs~
     */
    this.unsetBlobSet = function() {
        _blobset = undefined;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Define blobset variable.
     * @function setBlobSet
     * @memberOf ipol.DrawInputs~
     * @param {object} blobset
     */
    this.setBlobSet = function(blobset) {
        _blobset = blobset;
        if (blobset) {
            this.unsetUploadPageState();
        }
    }
    
    //     //--------------------------------------------------------------------------
    //     this.onLoadImages = function(callback) {
    //         this.onloadimages_cb = callback;
    //     }
    //     
    
    //--------------------------------------------------------------------------
    /**
     * Sets On Crop built callback
     * @function onCropBuilt
     * @memberOf ipol.DrawInputs~
     * @param {callback} callback sets oncropbuilt callback
     */
    this.onCropBuilt = function(callback) {
        _oncropbuilt_cb = callback;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Sets On  Load Images callback
     * @function onLoadImages
     * @memberOf ipol.DrawInputs~
     * @param {callback} callback sets onloadimages callback
     */
    this.onLoadImages = function(callback) {
        _onloadimages_cb = callback;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Checks if blobs has an image for input number idx (used?)
     * @function _blobHasImage
     * @memberOf ipol.DrawInputs~
     * @param {number} blob_idx
     * @returns {boolean}
     * @private
     */
    var _blobHasImage = function( blob_idx) {
        var image_found = false;
        var blobset = _blobset;
        if (blobset==null) {
            return false;
        }
        var inputs = _ddl_json.inputs;
        if (inputs[blob_idx].type!='image') {
            var blob_links = blobset[0].html_params.split('&');
            _infoMessage("blob_links = ", blob_links);
            for(var bid=1;bid<blob_links.length;bid++) {
                _infoMessage(" blob_idx = ", blob_idx, " ",parseInt(blob_links[bid].split(':')[0]));
                if ((parseInt(blob_links[bid].split(':')[0])===blob_idx) &&
                    (blob_links[bid].split(':')[1].toLowerCase().indexOf(".png")>-1) ) {
                    image_found = true;
                    _infoMessage("image found");
                    break;
                }
            }
        }
        return image_found;
    };
    
    //--------------------------------------------------------------------------
    /**
     * Create inputs HTML code
     * @function createHTML
     * @memberOf ipol.DrawInputs~
     * @public
     */
    this.createHTML = function() {
        
        // setting maxdim to half the screen width
        _draw_info.maxdim = window.screen.width/2;
        var html = "";
        var inputs = _ddl_json.inputs;
        
        // try to have nearest neighbor interpolation 
        // (see https://developer.mozilla.org/fr/docs/Web/CSS/Image-rendering)
        var img_style = "image-rendering:pixelated;"+
                        "-ms-interpolation-mode:nearest-neighbor;"+
                        "image-rendering:optimizeSpeed;"+
                        "image-rendering:-moz-crisp-edges;"+
                        "image-rendering:-o-crisp-edges;";
//                         "image-rendering:-webkit-optimize-contrast;"+
                        "image-rendering:optimize-contrast;"+
                        "image-rendering:crisp-edges;";

        // add features interface
        if (_drawfeature)   { html += _drawfeature.createHTML(); }
        
        // use gallery only if several images 
        if (inputs.length>1) {
            html += '<div id="input_gallery"> </div>';
        } else {
            // simple image output
            html += '<div style="clear:both"> </div>'+
                    '<table id="inputimage_table">'+
                    '<tr>'+
                        '<td><div id="inputimage_div" style="float:left;margin:0px;">'+
                            '<img  id="inputimage" crossOrigin="Anonymous"'+
                                'max-width:' +_draw_info.maxdim+'px;'+
                                'max-height:'+_draw_info.maxdim+'px;'+
                                'width:auto;height:auto;float:left"' +
                            '>'+
                        '</div></td>'+
                        '<td class="table_crop">'+
                            '<div id="previewimage" style="height:500px;float:left;margin:0px;'+img_style+'">'+
                                '<div class="preview"></div>'+
                            '</div>'+
                        '</td>'+
                    '</tr>'+
                    '<tr>'+
                        '<td style="text-align:center;">'+
                            // split cell using inside table
                            '<table style="width:100%;border:0;margin:0;padding:0;"><tr>'+
                            '<td style="border:0;margin:0;padding:0;" id="image_info"></td>'+
                            '<td style="border:0;width:4em;margin:0;padding:0;">'+
                                '<input id="id_cropinput" type="checkbox" >crop'+
                            '</td>'+
                            '<td style="border:0;width:4em;margin:0;padding:0;">'+
                                '<input id="id_cropview" type="checkbox" >view'+
                            '</td>'+
                            '</tr></table>'+
                        '</td>'+
                        '<td class="table_crop" id="crop_info" style="text-align:center;">'+
                            'crop info'+
                        '</td>'+
                    '</tr>'+
                    '</table>';

        }

        
        
        $("#DrawInputs").html(html);
        $('.table_crop').hide();
        $("#id_cropview").prop('disabled',false);
        
        // save object in DrawInputs HTML element
        $("#DrawInputs").data("draw_inputs",this);

        // add features events
        if (_drawfeature) { 
            html += _drawfeature.createHTMLEvents(); 
            $("#input_gallery").hide();
            $("#inputimage_table").hide();
        }
    };

    
    //--------------------------------------------------------------------------
    /**
     * Check is an image has been correctly loaded
     * code from https://stereochro.me/ideas/detecting-broken-images-js (used?)
     * @function _isImageOk
     * @memberOf ipol.DrawInputs~
     * @param {object} img input image
     * @return {boolean}
     * @private
     */
    var _isImageOk = function(img) {
        // During the onload event, IE correctly identifies any images that
        // weren’t downloaded as not complete. Others should too. Gecko-based
        // browsers act like NS4 in that they report this incorrectly.
        if ((!img)||(!img.complete)) {
            return false;
        }

        // However, they do have two very useful properties: naturalWidth and
        // naturalHeight. These give the true size of the image. If it failed
        // to load, either of these should be zero.
        if (typeof img.naturalWidth !== "undefined" && img.naturalWidth === 0) {
            return false;
        }

        // No other way of checking: assume it’s ok.
        return true;
    }

    //--------------------------------------------------------------------------
    /**
     * Update the page display after loading the input image for single input
     * demos.
     * @function _onLoadSingleImage
     * @memberOf ipol.DrawInputs~
     * @param {object} image input image
     * @private
     */
    var _onLoadSingleImage = function(image) { 
        _infoMessage("OnLoadSingleImage begin");
        var draw_info = _draw_info;
        var crop_info = _crop_info;
        // compute display ratio
        draw_info.display_ratio=(image.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/image.naturalWidth;
        //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
        _infoMessage("width ", image.naturalWidth ," display_ratio ", draw_info.display_ratio);
        $('#inputimage').attr("src", image.src);
        $('#inputimage_div').css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage_div').css ("width",  (image.naturalWidth *draw_info.display_ratio)+'px');
        $('#previewimage')  .css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage')    .attr("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#image_info').html(  Math.round(image.naturalWidth)+"x"+
                                Math.round(image.naturalHeight)+
                                " (x"+(draw_info.display_ratio).toFixed(2)+")");
        _updateCrop();
        crop_info.x = 0;
        crop_info.y = 0;
        crop_info.w = image.naturalWidth;
        crop_info.h = image.naturalHeight;
        _infoMessage("crop_info = ", crop_info);
        _infoMessage("OnLoadSingleImage end");
        // set feature drawing
        if (_drawfeature ) {
            // we assume that the first image is the input
            _drawfeature.updateDrawing(image);
        }
        if (_onloadimages_cb!=undefined) {
            _onloadimages_cb();
        }
        
    }
    
    //--------------------------------------------------------------------------
    /**
     * Creates an instance of ImageGallery object for multiple-input demos.
     * @function _createGallery
     * @memberOf ipol.DrawInputs~
     * @param {object} inputs_info list of input images and titles for the 
     * Image Gallery object
     * @private
     */
    var _createGallery = function(inputs_info) {

        var ig = new ipol.ImageGallery("inputs");
        ig.Append(inputs_info);
        if ((_drawfeature)&&(!inputs_info.Mask)) {
            ig.Append({ "Mask":"background_transparency.png"});
        }
        var html = ig.CreateHtml();
        $("#input_gallery").html(html);
        ig.CreateEvents();
        $("#input_gallery").data("image_gallery",ig);
        
        //-----------------------------------
        ig.SetOnLoad( function(index,image) {
            _infoMessage("OnLoad callback for image ",index);
            // several images, take crop info from first image
            if (index==0) {
                _crop_info.x = 0;
                _crop_info.y = 0;
                _crop_info.w = image.naturalWidth;
                _crop_info.h = image.naturalHeight;
            }
        }.bind(this) );
        
        //-----------------------------------
        ig.SetOnLoadAll( function() {
            // set draw mask
            if (_drawfeature) {
                // we assume that the first image is the input
                // and that the second image is the mask
                if (inputs_info.Mask) {
                    _drawfeature.updateDrawing(ig.GetImage(0)[0],
                                               ig.GetImage(1)[0]);
                } else {
                    _drawfeature.updateDrawing(ig.GetImage(0)[0]);
                }
            }
            if (_onloadimages_cb!=undefined) {
                _onloadimages_cb();
            }
        }.bind(this) );
        
        //-----------------------------------
        ig.SetOnDisplay( function(index) {
            var im = ig.GetImage(index)[0];
            var ratio = Math.round($("#input_gallery #img_"+index+"_0").width())/im.naturalWidth;
            var image_info = Math.round(im.naturalWidth)+"x"+
                                Math.round(im.naturalHeight)+
                                " (x"+(ratio).toFixed(3)+")";
            $('#input_gallery #inputinfo_'+index).html(image_info);
            ratio = Math.round($("#gallery_inputs_all #img_"+index+"_0").width())/im.naturalWidth;
            image_info = Math.round(im.naturalWidth)+"x"+
                                Math.round(im.naturalHeight)+
                                " (x"+(ratio).toFixed(3)+")";
            $('#gallery_inputs_all #inputinfo_'+index).html(image_info);
        }.bind(this));
        
        // we don't deal with crop with multiple inputs for the moment
        //             this.CreateCropper();
    }
    
    //--------------------------------------------------------------------------
    /**
     * Loads input data from the selected blobset. If the demo has several
     * inputs, creates the inputs information and instanciate the ImageGallery
     * class through the method CreateGallery, otherwise load a single image 
     * and call OnLoadSingleImage.
     * @function loadDataFromBlobSet
     * @memberOf ipol.DrawInputs~
     * @public
     */
    this.loadDataFromBlobSet = function() {

        var inputs  = _ddl_json.inputs;
        var blobset = _blobset;
        _input_origin = "blobset";

        // load input image ...
        var blobs_url_params = blobset[0].html_params.split('&');
        _infoMessage("blobs_url_params=",blobs_url_params);
        var blobs_url = blobs_url_params[0].split('=')[1];
        
        if (inputs.length>1) {
            // Create Gallery object
            var inputs_info = {};
            for(var idx=0;idx<inputs.length;idx++) {
                if (idx+1<blobs_url_params.length) {
                    var idx_str = blobs_url_params[idx+1].split(':')[0];
                    var blob    = blobs_url_params[idx+1].split(':')[1];
                    if (blob.indexOf(',')>-1) {
                        var blobs = blob.split(',');
                        for(var n=0;n<blobs.length;n++) {
                            if (blobs[n].toLowerCase().endsWith(".png")) {
                                blob = blobs[n];
                            }
                        }
                    }
                    var label = inputs[idx].description;
                    // set object input to have information text below the image
                    var obj = {};
                    obj['<span id="inputinfo_'+idx+'">img info</span>'] = blobs_url+blob;
                    inputs_info[label]= obj;
                }
            }
            _createGallery(inputs_info);
        } else {
            var blob      = blobset[0].html_params.split('&')[1].split(':')[1];
            if (inputs[0].type=="image") {
                var image = new Image();
                image.onload = function () {
                        _onLoadSingleImage(this);
                    };
                image.src = blobs_url+blob;
            } else {
                // extract non PNG file, ususally .txt for example
                if (blob.indexOf(',')>-1) {
                    var blobs = blob.split(',');
                    for(var n=0;n<blobs.length;n++) {
                        if (!blobs[n].toLowerCase().endsWith(".png")) {
                            blob = blobs[n];
                        }
                    }
                }
                jQuery.get(blobs_url+blob, undefined, function(data) {
                    // set feature drawing
                    if (_drawfeature) {
                        var feature_data = JSON.parse(data);
                        console.info("feature_data",feature_data);
                        // we assume that the first image is the input
                        _drawfeature.updateDrawing(feature_data);
                    }
                    if (_onloadimages_cb!=undefined) {
                        _onloadimages_cb();
                    }
                }, "text").done(function() {
                }).fail(function(jqXHR, textStatus) {
                }).always(function() {
                });
            }
        }
        _infoMessage("loadDataFromBlobSet end");
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Loads input data from the selected blobset. If the demo has several
     * inputs, creates the inputs information and instanciate the ImageGallery
     * class through the method CreateGallery, otherwise load a single image 
     * and call OnLoadSingleImage.
     * @function loadDataFromLocalFiles
     * @memberOf ipol.DrawInputs~
     * @public
     */
    this.loadDataFromLocalFiles = function() {
        var inputs  = _ddl_json.inputs;
        _input_origin = "localfiles";

        if (inputs.length>1) {
            var images = new Array(inputs.length);
            for(var idx=0;idx<inputs.length;idx++) {
                // input can be optional
                if ($('#localdata_preview_'+idx).attr("src")) {
                    images[idx] = new Image();
                    images[idx].src =  $('#localdata_preview_'+idx).attr("src");
                    //this.OnLoadImageFromMultiple(idx.toString(),images,images[idx]);
                }
            }

            // Create Gallery object
            var inputs_info = {};
            for(var idx=0;idx<inputs.length;idx++) {
                // image source could be missing if it is an optional input
                if (images[idx]) {
                    var label = inputs[idx].description;
                    // set object input to have information text below the image
                    var obj = {};
                    obj['<span id="inputinfo_'+idx+'">img info</span>'] = images[idx].src;
                    inputs_info[label]= obj;
                }
            }
            _createGallery(inputs_info);
        } else {
            if (inputs[0].type=="image") {
                var image = new Image();
                image.src =  $('#localdata_preview_0').attr("src");
                image.onload = function () {
                    _onLoadSingleImage(image);
                };
            } else {
                // TODO
//                 jQuery.get("foo.txt", undefined, function(data) {
//                     alert(data);
//                 }, "html").done(function() {
//                     alert("second success");
//                 }).fail(function(jqXHR, textStatus) {
//                     alert(textStatus);
//                 }).always(function() {
//                     alert("finished");
//                 });
            }
        }
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Unsets the upload page state 
     * @function unsetUploadPageState
     * @memberOf ipol.DrawInputs~
     * @returns {object} upload state object containing, for each input
     * index, the associated src_pos.
     * @public
     */
    this.unsetUploadPageState = function() {
        var inputs  = _ddl_json.inputs;
        for(var idx=0;idx<inputs.length;idx++) {
            $('#localdata_preview_'+idx).removeData();
        }
    }

    //--------------------------------------------------------------------------
    /**
     * @function setUploadPageState
     * @memberOf ipol.DrawInputs~
     * @param upload_state
     * @public
     */
    // return state:
    //  0: worked with changes
    //  1: failed since previous data is not available anymore
    //  2: no change
    this.setUploadPageState = function(upload_state) {
        this.unsetBlobSet();
        var inputs  = _ddl_json.inputs;
        var ok=true;
        var anychange=false;
        for(var idx=0;idx<inputs.length;idx++) {
            if (upload_state[idx]&&ipol.upload.last_uploaded_files[upload_state[idx]]) {
                var prev_data = $('#localdata_preview_'+idx).data("src_pos");
                if (prev_data!=upload_state[idx]) {
                    anychange=true;
                    $('#localdata_preview_'+idx).attr("src", 
                        ipol.upload.last_uploaded_files[upload_state[idx]]);
                    $('#localdata_preview_'+idx).data("src_pos",
                                                      upload_state[idx]);
                }
            } else {
                // ok if input not required, skip it
                ok=!_ddl_json.inputs[idx].required;
            }
        }
        if (!ok) {
            return 1;
        } else {
            if (anychange) {
                return 0;
            } else {
                return 2;
            }
        }
    }

    //--------------------------------------------------------------------------
    /**
     * Creates the cropper.
     * @function _createCropper
     * @memberOf ipol.DrawInputs~
     * @param upload_state
     * @private
     */
    var _createCropper = function() {
        _infoMessage("CreateCropper begin");
        var inputs  = _ddl_json.inputs;
        if (inputs.length===1) {
            var crop_enabled = $("#id_cropinput").is(':checked');
            if (crop_enabled) {
                
                _infoMessage("CreateCropper crop enabled");
                $("#inputimage").cropper({
                    viewMode: 0,
                    zoomOnWheel: false,
                    minCropBoxWidth : 10,
                    minCropBoxHeight: 10,
                    // adapted preview code from example customize-preview.html
                    build:  function (e) {
                        
                        var $clone = $(this).clone();

                        var crop_params = {
                            display: 'block',
                            width: '100%',
                            minWidth: 0,
                            minHeight: 0,
                            maxWidth: 'none',
                            maxHeight: 'none'
                        };
                        
                            
                        $clone.css(crop_params);

                        var $previews = $('.preview');
                        $previews.css({
                        height: '100%',
                        overflow: 'hidden'
                        }).html($clone);
                        
                    },
                    
                    built: function(cb) { return function(e) {
                        if (cb) {
                            console.info(" cropper built callback");
                            cb();
                        }
                    }}(_oncropbuilt_cb),

                    cropend: function(ddl_json) {
                        return function (e) {
                            // update parameters in case they depend on the crop
                            ipol.DrawParams.staticUpdateParams(ddl_json.params);
                        }
                    } (_ddl_json),
                                         

                    crop: function(crop_info, ddl_json) {
                        return function (e) {
//                             console.info("crop e=",e);
                            var imageData  = $(this).cropper('getImageData');
                            var canvasData = $(this).cropper('getCanvasData');
                            var ratio = imageData.width / imageData.naturalWidth;
                            
//                             console.info("*** ratio = ", ratio);
                            
                            if (ddl_json.general.hasOwnProperty('crop_maxsize')) {
                                var maxdim = eval(ddl_json.general.crop_maxsize);
//                                 console.info("maxdim = ",maxdim);
                            }
                            var resize=false;
                            if (Math.round(e.width)>maxdim) {
//                                 console.info("e.width = ", e.width);
                                e.width = maxdim;
                                resize=true;
                            }
                            if (Math.round(e.height)>maxdim) {
//                                 console.info("e.height = ", e.height);
                                // setting size in visual window pixels
                                e.height = maxdim;
                                resize=true;
                            }
                            if (resize) {
                                // setting size in visual window pixels
                                // inverse transform that the one used in
                                // getData from cropper.js (line 2395)
                                $(this).cropper('setCropBoxData',
                                                {   left:   e.x     *ratio + canvasData.left,
                                                    top:    e.y     *ratio + canvasData.top,
                                                    width:  e.width *ratio,
                                                    height: e.height*ratio});
                                return;
                            }
                            var previewAspectRatio = e.width / e.height;

                            var $previews = $('.preview');
                            $previews.each(function () {
                                var $preview = $(this);

                                var previewHeight = $preview.height();
                                var previewWidth  = previewHeight * previewAspectRatio;
                                var imageScaledRatio = e.width / previewWidth;
                                
                                if ($("#id_cropview").is(':checked')) {
                                    $("#crop_info").html(Math.round(e.width)+"x"+Math.round(e.height)+" (x"+(1/imageScaledRatio).toFixed(2)+")");
                                    $preview.width(previewWidth).find('img').css({
                                        width: imageData.naturalWidth / imageScaledRatio,
                                        height: imageData.naturalHeight / imageScaledRatio,
                                        marginLeft: -e.x / imageScaledRatio,
                                        marginTop: -e.y / imageScaledRatio
                                    });
                                }
                                crop_info.x = e.x;
                                crop_info.y = e.y;
                                crop_info.w = e.width;
                                crop_info.h = e.height;
//                                 console.info("callback crop_info=",crop_info);
                            });
                            
                        }
                    } (_crop_info, _ddl_json),
                                         
                });
                
                
            }
//             $('#inputimage_table td:nth-child(2)').show();
            if ($("#id_cropview").is(':checked')) {
                $('.table_crop').show();
            }
            $("#id_cropview").prop('disabled',false);
        } else {
//             $('#inputimage_table td:nth-child(2)').hide();
            $('.table_crop').hide();
            $("#id_cropview").prop('disabled',true);
        }
        _infoMessage("CreateCropper end");
    }
    
    //--------------------------------------------------------------------------
    /**
     * Destroys the cropper.
     * @function _destroyCropper
     * @memberOf ipol.DrawInputs~
     * @private
     */
    var _destroyCropper = function() {
        _infoMessage("DestroyCropper ");
        $("#inputimage").cropper('destroy');
        $('.table_crop').hide();
        $("#id_cropview").prop('disabled',true);
    }
    
    //--------------------------------------------------------------------------
    /**
     * Sets the crop area
     * @function setCrop
     * @memberOf ipol.DrawInputs~
     * @param {object} crop_area contains x,y,width,height
     * @public
     */
    this.setCrop = function(crop_area) {
        _infoMessage('setCrop begin ',crop_area);
        var imageData  = $("#inputimage").cropper('getImageData');
        var canvasData = $("#inputimage").cropper('getCanvasData');
        var ratio = imageData.width / imageData.naturalWidth;
        _infoMessage('ratio = ',ratio, ' imageData is ', imageData);
        _infoMessage('canvasData = ',canvasData);
        var box = {     left:   (crop_area.x      *ratio), //+ canvasData.left,
                        top:    (crop_area.y      *ratio), //+ canvasData.top,
                        width:  (crop_area.width  *ratio),
                        height: (crop_area.height *ratio)};
        _infoMessage("box=",box);
        $("#inputimage").cropper('setCropBoxData',box);
        _infoMessage('setCrop end');
    }

    //--------------------------------------------------------------------------
    /**
     * Updates the display of the crop area and the crop view 
     * based on the parameters
     * @function _updateCrop
     * @memberOf ipol.DrawInputs~
     * @param {object} crop_area contains x,y,width,height
     * @private
     */
    var _updateCrop = function() {
        _infoMessage("UpdateCrop begin");
        var inputs  = _ddl_json.inputs;
        if (inputs.length===1) {
            $("#id_cropinput").unbind().change( function()   { 
                _infoMessage("id_cropinput change event begin");
                _updateCrop(); 
                _infoMessage("id_cropinput change event end");
            }.bind(this));
            $("#id_cropview").unbind().change( function() {  
                if ($("#id_cropview").is(':checked')) { 
                    $('.table_crop').show();
                    // call move to update/display the crop view
                    $("#inputimage").cropper('move',0,0);
                } else {
                    $('.table_crop').hide();
                }
            }.bind(this));
            var crop_enabled = $("#id_cropinput").is(':checked');
            //console.info("setCrop ",  crop_enabled);
            if (crop_enabled) {
                _createCropper();
                _crop_info.enabled=true;
            } else {
                _destroyCropper();
                _crop_info.enabled=false;
                // reset crop info as full image
//                 console.info("natw = ", $('#inputimage').naturalWidth());
                _crop_info.x = 0;
                _crop_info.y = 0;
                _crop_info.w = $('#inputimage').naturalWidth();
                _crop_info.h = $('#inputimage').naturalHeight();
            }
        } else {
            _crop_info.enabled=false;
            // reset crop info as full image
            _crop_info.x = 0;
            _crop_info.y = 0;
            var ig = $("#input_gallery").data("image_gallery");
            _crop_info.w = ig.GetImage(0)[0].naturalWidth;
            _crop_info.h = ig.GetImage(0)[0].naturalHeight;
        }
        _infoMessage("UpdateCrop end");
        _infoMessage("cropinfo = ",_crop_info);
    }
    
};
