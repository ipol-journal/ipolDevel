/**
 * @file 
 * this file contains the code that renders the selected input blobs
 * including the option to crop the input image
 * associated with ipol_demo.html and ipol_demo.js
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";


//------------------------------------------------------------------------------
/**
 * DrawInputs interface
 * @constructor
 * @param {object} ddl_json Demo description object (DDL)
 */

var DrawInputs = function(ddl_json) {
    
    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function InfoMessage
     * @memberOf DrawInputs~
     */
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- DrawInputs ----");
            console.info.apply(console,args);
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Displays message in console independently of verbose 
     * @function PriorityMessage
     * @memberOf DrawInputs~
     */
    this.PriorityMessage = function( ) {
        var args = [].slice.call( arguments ); //Convert to array
        args.unshift("---- DrawInputs ----");
        console.info.apply(console,args);
    }
    
    //--------------------------------------------------------------------------
    // Initialize members
    //--------------------------------------------------------------------------
    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} verbose
     * @memberOf DrawInputs~
     */
    this.verbose=false;
    this.PriorityMessage(" DrawInput started ");
    /** 
     * The Demo Description Language DDL object.
     * @var {object} ddl_json
     * @memberOf DrawInputs~
     */
    this.ddl_json      = ddl_json;
    /** 
     * Contains image display constraints or information. 
     * For single image display, maxdim is set to 768 so that bigger images
     * will be scaled down. display_ratio is then the calculated display ratio.
     * For multiple images, maxdim will be calculated based on the available 
     * space of the webpage (window).
     * @var {{maxdim: number, display_ratio: number}} draw_info
     * @memberOf DrawInputs~
     */
    this.draw_info     = { maxdim:768,  display_ratio:-1};

    /** 
     * Stores the origin of the inputs, initialized to , it can be 
     * "blobset" or "localfiles".
     * @var {string} input_origin
     * @memberOf DrawInputs~
     */
    this.input_origin  = "";

    /** 
     * Contains the crop information: {enabled, x, y, w, h}.
     * @var {object} crop_info
     * @memberOf DrawInputs~
     */
    this.crop_info     = { enabled:false, x:0,y:0,w:1,h:1};

    /** 
     * id=progressbar selector.
     * @var {object} progressbar
     * @memberOf DrawInputs~
     */
    this.progressbar   = $("#progressbar");

    /** 
     * class=progresslabel selector.
     * @var {object} progresslabel
     * @memberOf DrawInputs~
     */
    this.progresslabel = $(".progress-label");

    /** 
     * callback called once crop is built.
     * @var {object} oncropbuilt_cb
     * @memberOf DrawInputs~
     */
    this.oncropbuilt_cb  = undefined;

    /** 
     * callback called once the images are loaded.
     * @var {object} onloadimages_cb
     * @memberOf DrawInputs~
     */
    this.onloadimages_cb = undefined;

    /** 
     * if inpainting is enabled, contains the Inpainting instance.
     * @var {object} inpaint
     * @memberOf DrawInputs~
     */
    // add inpainting features
    if (this.ddl_json.general.inpainting) {
        this.inpaint = new Inpainting();
    } else {
        this.inpaint = undefined;
    }

    
    //--------------------------------------------------------------------------
    /**
     * Undefine blobset variable.
     * @function UnsetBlobSet
     * @memberOf DrawInputs~
     */
    this.UnsetBlobSet = function() {
        this.blobset = undefined;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Define blobset variable.
     * @function SetBlobSet
     * @memberOf DrawInputs~
     * @param {object} blobset
     */
    this.SetBlobSet = function(blobset) {
        this.blobset = blobset;
        if (blobset) {
            this.UnsetUploadPageState();
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Get the blobsset.
     * @function GetBlobSet
     * @memberOf DrawInputs~
     * @returns {object}
     */
    this.GetBlobSet = function() {
        return this.blobset;
    }
    
//     //--------------------------------------------------------------------------
//     this.OnLoadImages = function(callback) {
//         this.onloadimages_cb = callback;
//     }
//     
    //--------------------------------------------------------------------------
    /**
     * Sets On Crop built callback
     * @function OnCropBuilt
     * @memberOf DrawInputs~
     * @param {callback} callback sets oncropbuilt callback
     */
    this.OnCropBuilt = function(callback) {
        this.oncropbuilt_cb = callback;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Sets On  Load Images callback
     * @function OnLoadImages
     * @memberOf DrawInputs~
     * @param {callback} callback sets onloadimages callback
     */
    this.OnLoadImages = function(callback) {
        this.onloadimages_cb = callback;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Checks if blobs has an image for input number idx
     * @function BlobHasImage
     * @memberOf DrawInputs~
     * @param {number} blob_idx
     * @returns {boolean}
     */
    this.BlobHasImage = function( blob_idx) {
        var image_found = false;
        var blobset = this.blobset;
        if (blobset==null) {
            return false;
        }
        var inputs = this.ddl_json.inputs;
        if (inputs[blob_idx].type!='image') {
            var blob_links = blobset[0].html_params.split('&');
            this.InfoMessage("blob_links = ", blob_links);
            for(var bid=1;bid<blob_links.length;bid++) {
                this.InfoMessage(" blob_idx = ", blob_idx, " ",parseInt(blob_links[bid].split(':')[0]));
                if ((parseInt(blob_links[bid].split(':')[0])===blob_idx) &&
                    (blob_links[bid].split(':')[1].toLowerCase().indexOf(".png")>-1) ) {
                    image_found = true;
                    this.InfoMessage("image found");
                    break;
                }
            }
        }
        return image_found;
    };
    
    //--------------------------------------------------------------------------
    /**
     * Create inputs HTML code
     * @function CreateHTML
     * @memberOf DrawInputs~
     */
    this.CreateHTML = function() {
        
        // setting maxdim to half the screen width
        this.draw_info.maxdim = window.screen.width/2;
        var html = "";
        var inputs = this.ddl_json.inputs;
        
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

        // add inpainting interface
        if (this.inpaint) { html += this.inpaint.CreateHTML(); }
        
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
                                'max-width:' +this.draw_info.maxdim+'px;'+
                                'max-height:'+this.draw_info.maxdim+'px;'+
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
        $("#DrawInputs").data("draw_inputs",this);

        if (this.inpaint) { 
            html += this.inpaint.CreateHTMLEvents(); 
            $("#input_gallery").hide();
        }
    };

    
    //--------------------------------------------------------------------------
    /**
     * Check is an image has been correctly loaded
     * code from https://stereochro.me/ideas/detecting-broken-images-js
     * @function IsImageOk
     * @memberOf DrawInputs~
     * @param {object} img input image
     * @return {boolean}
     */
    this.IsImageOk = function(img) {
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
     * @function OnLoadSingleImage
     * @memberOf DrawInputs~
     * @param {object} image input image
     */
    this.OnLoadSingleImage = function(image) { 
        this.InfoMessage("OnLoadSingleImage begin");
        var draw_info = this.draw_info;
        var crop_info = this.crop_info;
        // compute display ratio
        draw_info.display_ratio=(image.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/image.naturalWidth;
        //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
        this.InfoMessage("width ", image.naturalWidth ," display_ratio ", draw_info.display_ratio);
        $('#inputimage').attr("src", image.src);
        $('#inputimage_div').css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage_div').css ("width",  (image.naturalWidth *draw_info.display_ratio)+'px');
        $('#previewimage')  .css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage')    .attr("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#image_info').html(  Math.round(image.naturalWidth)+"x"+
                                Math.round(image.naturalHeight)+
                                " (x"+(draw_info.display_ratio).toFixed(2)+")");
        this.UpdateCrop();
        crop_info.x = 0;
        crop_info.y = 0;
        crop_info.w = image.naturalWidth;
        crop_info.h = image.naturalHeight;
        this.InfoMessage("crop_info = ", crop_info);
        this.InfoMessage("OnLoadSingleImage end");
        if (this.onloadimages_cb!=undefined) {
            this.onloadimages_cb();
        }
    }
    
    //--------------------------------------------------------------------------
    /**
     * Creates an instance of ImageGallery object for multiple-input demos.
     * @function CreateGallery
     * @memberOf DrawInputs~
     * @param {object} inputs_info list of input images and titles for the 
     * Image Gallery object
     */
    this.CreateGallery = function(inputs_info) {

        var ig = new ImageGallery("inputs");
        ig.Append(inputs_info);
        if ((this.inpaint)&&(!inputs_info.Mask)) {
            ig.Append({ "Mask":"background_transparency.png"});
        }
        var html = ig.CreateHtml();
        $("#input_gallery").html(html);
        ig.CreateEvents();
        $("#input_gallery").data("image_gallery",ig);
        
        //-----------------------------------
        ig.SetOnLoad( function(index,image) {
            this.InfoMessage("OnLoad callback for image ",index);
            // several images, take crop info from first image
            if (index==0) {
                this.crop_info.x = 0;
                this.crop_info.y = 0;
                this.crop_info.w = image.naturalWidth;
                this.crop_info.h = image.naturalHeight;
            }
        }.bind(this) );
        
        //-----------------------------------
        ig.SetOnLoadAll( function() {
            // set inpainting
            if (this.inpaint) {
                // we assume that the first image is the input
                // and that the second image is the mask
                if (inputs_info.Mask) {
                    this.inpaint.UpdateInpaint(ig.GetImage(0)[0],ig.GetImage(1)[0]);
                } else {
                    this.inpaint.UpdateInpaint(ig.GetImage(0)[0]);
                }
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
     * @function LoadDataFromBlobSet
     * @memberOf DrawInputs~
     */
    this.LoadDataFromBlobSet = function() {

        var inputs  = this.ddl_json.inputs;
        var blobset = this.blobset;
        this.input_origin = "blobset";

        // load input image ...
        var blobs_url_params = blobset[0].html_params.split('&');
        this.InfoMessage("blobs_url_params=",blobs_url_params);
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
            this.CreateGallery(inputs_info);
        } else {
            var blob      = blobset[0].html_params.split('&')[1].split(':')[1];
            var image = new Image();
            image.onload = (function(drawinputs) { 
                return function () {
                    drawinputs.OnLoadSingleImage(this);
                };
            })(this);
            image.src = blobs_url+blob;
        }
        this.InfoMessage("LoadDataFromBlobSet end");
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Loads input data from the selected blobset. If the demo has several
     * inputs, creates the inputs information and instanciate the ImageGallery
     * class through the method CreateGallery, otherwise load a single image 
     * and call OnLoadSingleImage.
     * @function LoadDataFromLocalFiles
     * @memberOf DrawInputs~
     */
    this.LoadDataFromLocalFiles = function() {
        var inputs  = this.ddl_json.inputs;
        this.input_origin = "localfiles";

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
            this.CreateGallery(inputs_info);
        } else {
            var image = new Image();
            image.src =  $('#localdata_preview_0').attr("src");
            image.onload = function () {
               this.OnLoadSingleImage(image);
            }.bind(this);
        }
    };
    
    
    //--------------------------------------------------------------------------
    /**
     * Gets the upload window state for browser history events. Uploaded file
     * are stored in $('#localdata_preview_'+idx).data("src_pos")
     * @function GetUploadPageState
     * @memberOf DrawInputs~
     * @returns {object} upload state object containing, for each input
     * index, the associated src_pos.
     */
    this.GetUploadPageState = function() {
        var upload_state = {};
        var inputs  = this.ddl_json.inputs;
        for(var idx=0;idx<inputs.length;idx++) {
            upload_state[idx] =  $('#localdata_preview_'+idx).data("src_pos");
        }
        return upload_state;
    }
    
    //--------------------------------------------------------------------------
    /**
     * Unsets the upload page state freeing thee
     * @function UnsetUploadPageState
     * @memberOf DrawInputs~
     * @returns {object} upload state object containing, for each input
     * index, the associated src_pos.
     */
    this.UnsetUploadPageState = function() {
        var inputs  = this.ddl_json.inputs;
        for(var idx=0;idx<inputs.length;idx++) {
            $('#localdata_preview_'+idx).removeData();
        }
    }

    //--------------------------------------------------------------------------
    /**
     * @function SetUploadPageState
     * @memberOf DrawInputs~
     * @param upload_state
     */
    // return state:
    //  0: worked with changes
    //  1: failed since previous data is not available anymore
    //  2: no change
    this.SetUploadPageState = function(upload_state) {
        this.UnsetBlobSet();
        var inputs  = this.ddl_json.inputs;
        var ok=true;
        var anychange=false;
        for(var idx=0;idx<inputs.length;idx++) {
            if (upload_state[idx]&&last_uploaded_files[upload_state[idx]]) {
                var prev_data = $('#localdata_preview_'+idx).data("src_pos");
                if (prev_data!=upload_state[idx]) {
                    anychange=true;
                    $('#localdata_preview_'+idx).attr("src", last_uploaded_files[upload_state[idx]]);
                    $('#localdata_preview_'+idx).data("src_pos",upload_state[idx]);
                }
            } else {
                ok=false;
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
     * @function CreateCropper
     * @memberOf DrawInputs~
     * @param upload_state
     */
    this.CreateCropper = function() {
        this.InfoMessage("CreateCropper begin");
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            var crop_enabled = $("#id_cropinput").is(':checked');
            if (crop_enabled) {
                
                this.InfoMessage("CreateCropper crop enabled");
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
                    }}(this.oncropbuilt_cb),

                    cropend: function(ddl_json) {
                        return function (e) {
                            // update parameters in case they depend on the crop
                            ipol_params.UpdateParams(ddl_json.params);
                        }
                    } (this.ddl_json),
                                         

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
                    } (this.crop_info, this.ddl_json),
                                         
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
        this.InfoMessage("CreateCropper end");
    }
    
    //--------------------------------------------------------------------------
    /**
     * Destroys the cropper.
     * @function DestroyCropper
     * @memberOf DrawInputs~
     */
    this.DestroyCropper = function() {
        this.InfoMessage("DestroyCropper ");
        $("#inputimage").cropper('destroy');
//         $('#inputimage_table td:nth-child(2)').hide();
        $('.table_crop').hide();
        $("#id_cropview").prop('disabled',true);
    }
    
    //--------------------------------------------------------------------------
    /**
     * Sets the crop area
     * @function SetCrop
     * @memberOf DrawInputs~
     * @param {object} crop_area contains x,y,width,height
     */
    this.SetCrop = function(crop_area) {
        this.InfoMessage('SetCrop begin ',crop_area);
        var imageData  = $("#inputimage").cropper('getImageData');
        var canvasData = $("#inputimage").cropper('getCanvasData');
        var ratio = imageData.width / imageData.naturalWidth;
        this.InfoMessage('ratio = ',ratio, ' imageData is ', imageData);
        this.InfoMessage('canvasData = ',canvasData);
        var box = {     left:   (crop_area.x      *ratio), //+ canvasData.left,
                        top:    (crop_area.y      *ratio), //+ canvasData.top,
                        width:  (crop_area.width  *ratio),
                        height: (crop_area.height *ratio)};
        this.InfoMessage("box=",box);
        $("#inputimage").cropper('setCropBoxData',box);
        this.InfoMessage('SetCrop end');
    }

    //--------------------------------------------------------------------------
    /**
     * Updates the display of the crop area and the crop view 
     * based on the parameters
     * @function UpdateCrop
     * @memberOf DrawInputs~
     * @param {object} crop_area contains x,y,width,height
     */
    this.UpdateCrop = function() {
        this.InfoMessage("UpdateCrop begin");
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            $("#id_cropinput").unbind().change( function()   { 
                this.InfoMessage("id_cropinput change event begin");
                this.UpdateCrop(); 
                this.InfoMessage("id_cropinput change event end");
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
            //console.info("SetCrop ",  crop_enabled);
            if (crop_enabled) {
                this.CreateCropper();
                this.crop_info.enabled=true;
            } else {
                this.DestroyCropper();
                this.crop_info.enabled=false;
                // reset crop info as full image
//                 console.info("natw = ", $('#inputimage').naturalWidth());
                this.crop_info.x = 0;
                this.crop_info.y = 0;
                this.crop_info.w = $('#inputimage').naturalWidth();
                this.crop_info.h = $('#inputimage').naturalHeight();
            }
        } else {
            this.crop_info.enabled=false;
            // reset crop info as full image
            this.crop_info.x = 0;
            this.crop_info.y = 0;
            var ig = $("#input_gallery").data("image_gallery");
            this.crop_info.w = ig.GetImage(0)[0].naturalWidth;
            this.crop_info.h = ig.GetImage(0)[0].naturalHeight;
        }
        this.InfoMessage("UpdateCrop end");
        this.InfoMessage("cropinfo = ",this.crop_info);
    }
    
    //--------------------------------------------------------------------------
    /**
     * Initializes the progress bar and sets its events
     * @function InitProgress
     * @memberOf DrawInputs~
     */
    this.InitProgress = function() {

        this.InfoMessage("InitProgress");
        $( "#run_button" ).unbind("click").prop("disabled",true);
        this.starttime = 0;
        this.progress_info = "";
 
        this.progressbar.progressbar({
            value: 100,
            change: function() {
                var current_time = new Date().getTime();
                var elapsed = current_time-this.starttime;
                // in the first two seconds, show time every 0.1 sec
                if (elapsed<2000) {
                    this.progresslabel.text(  this.progress_info + " " + 
                                              Math.round(elapsed/100)/10 + " sec." );
                } else {
                    // then show time every sec.
                    this.progresslabel.text(  this.progress_info + " " + 
                                              Math.round(elapsed/1000) + " sec." );
                }
            }.bind(this),
            complete: function() {
                this.progresslabel.text( this.progress_info );
            }.bind(this)
        });
        
        this.InfoMessage("progresslabel= ", this.progresslabel);
        this.progresslabel.text("");
    }
    
    //--------------------------------------------------------------------------
    /**
     * Initializes the progress bar and sets its events, sets timeout events
     * it update itself, unless it has reached 100%
     * @function progress
     * @memberOf DrawInputs~
     * @param {object} start time, if defined, gets the current time
     * in the member variable starttime
     */
    this.progress = function( start) {
        var val = this.progressbar.progressbar( "value" );
        if (start!==undefined) {
            this.starttime = new Date().getTime();
            val=start;
        }
        this.progressbar.progressbar( "value", val + 2 );
        if ( val < 99 ) {
            var current_time = new Date().getTime();
            var elapsed = current_time-this.starttime;
            // if less than 2 sec, show progress every 1/10 sec
            if (elapsed<2000) {
                setTimeout( this.progress.bind(this), 100 );
            } else {
                // if less than 20 sec, show progress every sec
                if (elapsed<20000) {
                    setTimeout( this.progress.bind(this), 1000 );
                } else {
                // otherwise show progress every 2 sec.
                    setTimeout( this.progress.bind(this), 2000 );
                }
            }
        }
    }


    //--------------------------------------------------------------------------
    /**
     * Uploads the form that contains the input blobs and runs the demo 
     * note: we can´t upload through the proxy for the moment, so we need to 
     * use the demorunner address
     * @function UploadForm
     * @memberOf DrawInputs~
     * @param {object} form_data contains the data to upload
     */
    this.UploadForm = function( form_data) {
        $.ajax(servers.demorunner+"input_upload",
        {
            method: "POST",
            data: form_data,
            processData: false,
            contentType: false,
            //Do not cache the page
            cache: false,
            success: function ( res) {
                console.log('Upload success res=',res);
                this.progress_info = "upload success";
                this.RunDemo(JSON.parse(res));

            }.bind(this),
            error: function ( res) {
                console.log('Upload error res=',res);
                this.progress_info = "upload failure";
                this.progress(100);
            }.bind(this)
        });
    };

                        
    //--------------------------------------------------------------------------
    /**
     * @function json2uri
     * @memberOf DrawInputs~
     * @param {object} json
     */
    this.json2uri = function(json) {
            return encodeURIComponent(JSON.stringify(json));
    }
        
    //--------------------------------------------------------------------------
    /**
     * @function ResultProgress
     * @memberOf DrawInputs~
     * @param {object} run_demo_res
     */
    this.ResultProgress = function(run_demo_res) {
        if (run_demo_res.status==="KO") {
            this.PriorityMessage(" Failure demo run run_demo_res:",run_demo_res);
            this.progress_info = "run_demo:failure";
            this.progress(100);
        } else {
            // stop progress
            this.progress_info = "success (ran in "+ run_demo_res.algo_info.run_time.toPrecision(2)+" s)";
            this.progress(100);
        }
        //this.progressbar.progressbar( "complete" );
    }
    
    //--------------------------------------------------------------------------
    /**
     * runs the demo once the input(s) are selected (and cropped) or uploaded
     * @function RunDemo
     * @memberOf DrawInputs~
     * @param {object} res result obtained from upload or select and crop
     * calls to demorunner
     */
    this.RunDemo = function(res) {
        
        this.PriorityMessage("upload/select&crop res=", res);
        
        if (res.status==="KO") {
            this.progress_info = "upload/select&crop:failure";
            this.progress(100);
            return;
        } else {
            // reset progress after build
            //this.progress(0);
        }
        // create parameters
        if (this.ddl_json.params) {
            var params = ipol_params.GetParamValues(this.ddl_json.params);
        } else {
            var params = {};
        }
        // add crop info as parameters (would only need image size...)
        params['x0']=Math.round(this.crop_info.x);
        params['x1']=Math.round(this.crop_info.x+this.crop_info.w);
        params['y0']=Math.round(this.crop_info.y);
        params['y1']=Math.round(this.crop_info.y+this.crop_info.h);
        this.InfoMessage("params = ",params);
        // create meta information
        var meta={};
        if (res["process_inputs_msg"]!=undefined) {
            this.InfoMessage("adding message to meta data ");
            meta["process_inputs_msg"] = res["process_inputs_msg"];
        }
        meta["max_width"]  = res["max_width"];
        meta["max_height"] = res["max_height"];
        meta["original"]   = (this.input_origin==="localfiles")
        
        this.progress_info = "run_demo";
        
        // run_demo needs inputs, config and run from ddl_json
        var ddl_json_parts = {};
        ddl_json_parts['inputs']  = this.ddl_json.inputs;
        ddl_json_parts['config']  = this.ddl_json.config;
        ddl_json_parts['run']     = this.ddl_json.run;
        ddl_json_parts['archive'] = this.ddl_json.archive;
        // sending the result section seems problematic some some demos 
        // (like optical flow demos for example)
        
        // run demo
        var url_params = "demo_id="+this.ddl_json.demo_id+
                    "&key="+res.key+
                    "&ddl_json="+this.json2uri(ddl_json_parts)+
                    "&params=" +this.json2uri(params)+
                    "&meta=" +this.json2uri(meta);
        ipol_utils.ModuleService("demorunner","run_demo",url_params,
            function(run_demo_res) {
                this.ResultProgress(run_demo_res);
                if ((run_demo_res.status==="KO")&&
                    (!this.ddl_json.general['show_results_on_error'])) {
                        return;
                }
                this.PriorityMessage("run_demo run_demo_res=", run_demo_res);

                // push state will trigger result drawing ...
//                 // draw the results
//                 var dr = new DrawResults( run_demo_res, this.ddl_json.results );
//                 dr.Create();
                
                // Set url state for browser history
                var new_state={
                    demo_id       : this.ddl_json.demo_id,
                    state         : 2,
                    res           : run_demo_res,
                    ddl_json      : this.ddl_json,
                    scrolltop     : $(window).scrollTop(),
                    crop_checked  : $("#id_cropinput").is(':checked')
                };
                // add blobset info if input if from the proposed blobsets
                if (this.blobset) {
                    new_state["blobset"]      = this.blobset;
                } else {
                    new_state["upload_state"] = this.GetUploadPageState();
                }
                
                try {
                    // change url hash
                    History.pushState(
                        new_state,
                        "IPOL Journal - "+this.ddl_json.general.demo_title,
                        //"IPOLDemos "+this.ddl_json.demo_id+" results",
                        "?id="+this.ddl_json.demo_id+"&res="+this.json2uri(run_demo_res));
                } catch(err) {
                    console.error("error:", err.message);
                }
                
                // send to archive
                if (run_demo_res.send_archive) {
                    var url_params =    'demo_id='    + this.ddl_json.demo_id + 
                                        "&blobs="     + this.json2uri(run_demo_res.archive_blobs) + 
                                        "&parameters="+ this.json2uri(run_demo_res.archive_params);
                    ipol_utils.ModuleService("archive","add_experiment",url_params,
                                  function(archive_res) {
                                      console.info("archive add_experiment archive_res=",archive_res);
                                  });
                }
            }.bind(this)
        ).fail  ( function() {                             
                    this.progress_info = "failure";
                    this.progress(100); }.bind(this)
                );
            // end of run_demo
    }    
    
    //--------------------------------------------------------------------------
    /**
     * Sets the 'run' button click event, to call demorunner for upload,
     * select blobset with crop or initialize without inputs
     * @function SetRunEvent
     * @memberOf DrawInputs~
     */
    this.SetRunEvent = function() {
        this.InitProgress();
        $( "#run_button" ).unbind("click").prop("disabled",false);
        $( "#run_button" ).click( 
        function(){
            var ptext=this.progresslabel.text();
            // disable future clicks until run is finished
            this.progresslabel.text( "" );
            this.progress(0);
            this.progress_info = "initialization (check/build source code)";
            var url_params =   "demo_id="+this.ddl_json.demo_id+
                            "&ddl_build="+this.json2uri(this.ddl_json.build);
            // code to be executed on click
            ipol_utils.ModuleService("demorunner","init_demo", url_params,
            function(res) {
                console.info("init_demo res=", res);
                if (res.status==="KO") {
                    this.progress_info = "init_demo:failure";
                    this.progress(100);
                    return;
                }
                // select input from blobset or upload from local files
                console.info("input_origin = ", this.input_origin);
                if (this.inpaint) {
                    this.inpaint.SubmitInpaint(this.ddl_json,
                                               this.UploadForm.bind(this));
                } else {
                    switch (this.input_origin) {
                        case "blobset":
                            // need to deal with inpainting ...
                            // Set inputs using blobset
                            // crop at the same time
                            this.progress_info = "input selection and crop";
                            url_params= "demo_id="+this.ddl_json.demo_id+
                                    "&ddl_inputs="+this.json2uri(this.ddl_json.inputs)+
                                    "&"+this.blobset[0].html_params+
                                    "&crop_info="+this.json2uri(this.crop_info)
                            ipol_utils.ModuleService("demorunner","input_select_and_crop",url_params,
                                                this.RunDemo.bind(this)
                            ); // end input_select_and_crop
                            break;

                        case "localfiles":
                            // upload files and run the demo
                            this.progress_info = "input upload";

                            // fill form data to upload
                            var formData = new FormData();
                            formData.append('demo_id',    this.ddl_json.demo_id);
                            formData.append('ddl_inputs', JSON.stringify(this.ddl_json.inputs));
                            var inputs  = this.ddl_json.inputs;
                            if (inputs.length===1) {
                                // Upload cropped image to server if the browser supports `HTMLCanvasElement.toBlob`
                                var crop_enabled = $("#id_cropinput").is(':checked');
                                if (crop_enabled) {
                                    var cropped_canvas = $("#inputimage").cropper('getCroppedCanvas');
                                    cropped_canvas.toBlob( 
                                        function(blob) {
                                            console.info('adding blob (cropped) : ', blob);
                                            formData.append('file_0', blob);
                                            this.UploadForm(formData);
                                        }.bind(this), 'image/png' );
                                } else {
                                    var image_src = $("#inputimage").attr('src');
                                    blobUtil.imgSrcToBlob(image_src).then(
                                        function(blob) {
                                            formData.append('file_0', blob);
                                            this.UploadForm(formData);
                                        }.bind(this), 'image/png' );
                                }
                            } else {
                                // if several input image, TODO: deal with crop of first image
                                var blobs_in_form=0;
                                var image_src = [];
                                var nb_uploads = 0;
                                for(var idx=0;idx<inputs.length;idx++) {
                                    var src = $('#localdata_preview_'+idx).attr("src");
                                    // TODO: if image is not optional and src is undefined
                                    // send error
                                    if (src) {
                                        image_src[idx] = src;
                                        nb_uploads++;
                                    }
                                }
                                
                                for(var idx=0;idx<inputs.length;idx++) {
                                    if (image_src[idx]) {
                                        blobUtil.imgSrcToBlob(image_src[idx]).then(
                                            function(idx,obj) { return function(blob) {
                                                console.info('idx=',idx);
                                                formData.append('file_'+idx, blob);
                                                blobs_in_form++;
                                                console.info('blobs_in_form=',blobs_in_form);
                                                if(blobs_in_form==nb_uploads) {
                                                    obj.UploadForm(formData);
                                                }
                                            }
                                            }(idx,this), 'image/png' );
                                    }
                                }
                            }
                            break;
                            
                        case "noinputs":
                            // Set inputs using blobset
                            // crop at the same time
                            this.progress_info = "initialize with no inputs";
                            url_params= "demo_id="+this.ddl_json.demo_id
                            ipol_utils.ModuleService("demorunner","init_noinputs",url_params,
                                                this.RunDemo.bind(this)
                            ); // end input_select_and_crop
                            break;
                    } // end switch input_origin
                } // end if (inpaint)
            }.bind(this)
            ); // end init_demo
        }.bind(this)
        );
    }
    
};
