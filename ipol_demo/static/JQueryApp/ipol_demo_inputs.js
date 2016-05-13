//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_inputs.js
// date: march 2016
// author: Karl Krissian
//
// description:
// this file contains the code that renders the selected input blobs
// including the option to crop the input image
// associated with ipol_demo.html and ipol_demo.js
//

"use strict";


var DrawInputs = function(ddl_json) {
    
    //--------------------------------------------------------------------------
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- DrawInputs ----");
            console.info.apply(console,args);
        }
    }
    
    //--------------------------------------------------------------------------
    this.PriorityMessage = function( ) {
        var args = [].slice.call( arguments ); //Convert to array
        args.unshift("---- DrawInputs ----");
        console.info.apply(console,args);
    }
    
    this.verbose=false;
    this.PriorityMessage(" DrawInput started ");
    
    this.ddl_json      = ddl_json;
    this.draw_info     = { maxdim:768,  display_ratio:-1};
    this.input_origin  = "";
    this.crop_info     = { enabled:false, x:0,y:0,w:1,h:1};
    this.progressbar   = $("#progressbar");
    this.progresslabel = $(".progress-label");
    this.oncropbuilt_cb = undefined;
    
    //--------------------------------------------------------------------------
    this.SetBlobSet = function(blobset) {
        this.blobset = blobset;
    }
    
//     //--------------------------------------------------------------------------
//     this.OnLoadImages = function(callback) {
//         this.onloadimages_cb = callback;
//     }
//     
    //--------------------------------------------------------------------------
    this.OnCropBuilt = function(callback) {
        this.oncropbuilt_cb = callback;
    }
    
    //--------------------------------------------------------------------------
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
    this.CreateHTML = function() {
        
        // setting maxdim to half the screen width
        this.draw_info.maxdim = window.screen.width/2;
        var html = "";
        var inputs = this.ddl_json.inputs;
        
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
                            '<div id="previewimage" style="height:500px;float:left;margin:0px">'+
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
                    '</table>'+
                    '<div style="clear:both"> </div> <br/>';
        }
        $("#DrawInputs").html(html);
        $('.table_crop').hide();
        $("#id_cropview").prop('disabled',false);
        $("#DrawInputs").data("draw_inputs",this);
    };

    
    //--------------------------------------------------------------------------
    // code from https://stereochro.me/ideas/detecting-broken-images-js
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
    // on load a single input image
    this.OnLoadSingleImage = function(image) { 
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
        this.InfoMessage("onload function end");
        
    }
    
    //--------------------------------------------------------------------------
    this.CreateGallery = function(inputs_info) {

        var ig = new ImageGallery("inputs");
        ig.Append(inputs_info);
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
    this.LoadDataFromLocalFiles = function() {
        var inputs  = this.ddl_json.inputs;
        this.input_origin = "localfiles";

        if (inputs.length>1) {
            var images = new Array(inputs.length);
            for(var idx=0;idx<inputs.length;idx++) {
                images[idx] = new Image();
                images[idx].src =  $('#localdata_preview_'+idx).attr("src");
                //this.OnLoadImageFromMultiple(idx.toString(),images,images[idx]);

            }

            // Create Gallery object
            var inputs_info = {};
            for(var idx=0;idx<inputs.length;idx++) {
                var label = inputs[idx].description;
                // set object input to have information text below the image
                var obj = {};
                obj['<span id="inputinfo_'+idx+'">img info</span>'] = images[idx].src;
                inputs_info[label]= obj;
            }
            this.CreateGallery(inputs_info);
        } else {
            var image = new Image();
            image.src =  $('#localdata_preview_0').attr("src");
            this.OnLoadSingleImage(image);
        }
    };
    

    //--------------------------------------------------------------------------
    this.CreateCropper = function() {
        this.InfoMessage("CreateCropper ");
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            var crop_enabled = $("#id_cropinput").is(':checked');
            if (crop_enabled) {
                
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
                            cb();
                        }
                    }}(this.oncropbuilt_cb),

                    cropend: function(ddl_json) {
                        return function (e) {
                            // update parameters in case they depend on the crop
                            UpdateParams(ddl_json.params);
                        }
                    } (this.ddl_json),
                                         

                    crop: function(crop_info, ddl_json) {
                        return function (e) {
//                             console.info("crop e=",e);
                            var imageData  = $(this).cropper('getImageData');
                            var canvasData = $(this).cropper('getCanvasData');
                            var ratio = imageData.width / imageData.naturalWidth;
                            
//                             console.info("*** ratio = ", ratio);
                            
                            if (ddl_json.general.hasOwnProperty('crop_maxsize_new')) {
                                var maxdim = eval(ddl_json.general.crop_maxsize_new);
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
    }
    
    //--------------------------------------------------------------------------
    this.DestroyCropper = function() {
        this.InfoMessage("DestroyCropper ");
        $("#inputimage").cropper('destroy');
//         $('#inputimage_table td:nth-child(2)').hide();
        $('.table_crop').hide();
        $("#id_cropview").prop('disabled',true);
    }
    
    //--------------------------------------------------------------------------
    this.SetCrop = function(crop_area) {
        this.InfoMessage('SetCrop ',crop_area);
        var imageData  = $("#inputimage").cropper('getImageData');
        var canvasData = $("#inputimage").cropper('getCanvasData');
        var ratio = imageData.width / imageData.naturalWidth;
        this.InfoMessage('ratio = ',ratio);
        this.InfoMessage('canvasData = ',canvasData);
        ratio=1;
        var box = {   left:   crop_area.x     *ratio , //+ canvasData.left,
                            top:    crop_area.y     *ratio , //+ canvasData.top,
                            width:  crop_area.width *ratio,
                            height: crop_area.height*ratio};
        this.InfoMessage("box=",box);
        $("#inputimage").cropper('setCropBoxData',box);
    }

    //--------------------------------------------------------------------------
    this.UpdateCrop = function() {
//         console.info("SetCrop begin");
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            $("#id_cropinput").change( function() { this.UpdateCrop(); }.bind(this));
            $("#id_cropview").change( function() {  
                if ($("#id_cropview").is(':checked')) { 
                    $('.table_crop').show();
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
            this.crop_info.w = $('#img_0_0').naturalWidth();
            this.crop_info.h = $('#img_0_0').naturalHeight();
        }
//         console.info("SetCrop end");
        this.InfoMessage("cropinfo = ",this.crop_info);
    }
    
    
    //--------------------------------------------------------------------------
    this.InitProgress = function() {

        this.InfoMessage("InitProgress");
        this.progressbar.unbind("click");
        this.starttime = 0;
        this.progress_info = "";
 
        this.progressbar.progressbar({
            value: 100,
            change: function() {
                var current_time = new Date().getTime();
                var elapsed = current_time-this.starttime;
                if (elapsed<2000) {
                    this.progresslabel.text(  this.progress_info + " " + 
                                              Math.round(elapsed/100)/10 + " sec." );
                } else {
                    this.progresslabel.text(  this.progress_info + " " + 
                                              Math.round(elapsed/1000) + " sec." );
                }
            }.bind(this),
            complete: function() {
                this.progresslabel.text( this.progress_info + " " + "Rerun" );
            }.bind(this)
        });
        
        this.InfoMessage("progresslabel= ", this.progresslabel);
        this.progresslabel.text("Run");
    }
    
    //--------------------------------------------------------------------------
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
            if (elapsed<2000) {
                setTimeout( this.progress.bind(this), 100 );
            } else {
                if (elapsed<20000) {
                    setTimeout( this.progress.bind(this), 1000 );
                } else {
                    setTimeout( this.progress.bind(this), 2000 );
                }
            }
        }
    }


    //--------------------------------------------------------------------------
    // Uploads the form that contains the input blobs and runs the demo 
    this.UploadForm = function() {
        $.ajax(servers.demorunner+"input_upload",
        {
            method: "POST",
            data: this.formData,
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
    this.json2uri = function(json) {
            return encodeURIComponent(JSON.stringify(json));
    }
        
    //--------------------------------------------------------------------------
    // runs the demo once the input(s) are selected (and cropped) or uploaded
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
            var params = GetParamValues(this.ddl_json.params);
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
        ModuleService("demorunner","run_demo",url_params,
            function(res) {
                if (res.status==="KO") {
                    this.PriorityMessage("demo run res:",res);
                    this.progress_info = "run_demo:failure";
                    this.progress(100);
                    if (!this.ddl_json.general['show_results_on_error']) {
                        return;
                    }
                } else {
                    // stop progress
                    this.progress_info = "success (ran in "+ res.algo_info.run_time.toPrecision(2)+" s)";
                    this.progress(100);
                }
                this.PriorityMessage("run_demo res=", res);

                // push state will trigger result drawing ...
//                 // draw the results
//                 var dr = new DrawResults( res, this.ddl_json.results );
//                 dr.Create();
                
                // Set url state for browser history
                try {
                    var new_state={
                        demo_id:this.ddl_json.demo_id,
                        state:2,
                        res:res,
                        ddl_json:this.ddl_json
                    };
                    // add blobset info if input if from the proposed blobsets
                    if (this.blobset) {
                        new_state["blobset"]      = this.blobset;
                        new_state["crop_checked"] = $("#id_cropinput").is(':checked');
                    }
                    // change url hash
                    History.pushState(
                        new_state,
                        "IPOLDemos "+this.ddl_json.demo_id+" results",
                        "?id="+this.ddl_json.demo_id+"&res="+this.json2uri(res));
                } catch(err) {
                    console.error("error:", err.message);
                }
                
                // send to archive
                if (res.send_archive) {
                    var url_params =    'demo_id='    + this.ddl_json.demo_id + 
                                        "&blobs="     + this.json2uri(res.archive_blobs) + 
                                        "&parameters="+ this.json2uri(res.archive_params);
                    ModuleService("archive","add_experiment",url_params,
                                  function(res) {
                                      console.info("archive add_experiment res=",res);
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
    this.SetRunEvent = function() {
        this.InitProgress();
        this.progressbar.click( 
        function(){
            var ptext=this.progresslabel.text();
            if (ptext.endsWith("Rerun")||ptext.endsWith("Run"  )) {
                // disable future clicks until run is finished
                this.progresslabel.text( "" );
                this.progress(0);
                this.progress_info = "initialization (check/build source code)";
                var url_params =   "demo_id="+this.ddl_json.demo_id+
                                "&ddl_build="+this.json2uri(this.ddl_json.build);
                // code to be executed on click
                ModuleService("demorunner","init_demo", url_params,
                function(res) {
                    console.info("init_demo res=", res);
                    if (res.status==="KO") {
                        this.progress_info = "init_demo:failure";
                        this.progress(100);
                        return;
                    }
                    // select input from blobset or upload from local files
                    console.info("input_origin = ", this.input_origin);
                    if (this.input_origin==="blobset") {
                        // Set inputs using blobset
                        // crop at the same time
                        this.progress_info = "input selection and crop";
                        url_params= "demo_id="+this.ddl_json.demo_id+
                                 "&ddl_inputs="+this.json2uri(this.ddl_json.inputs)+
                                 "&"+this.blobset[0].html_params+
                                 "&crop_info="+this.json2uri(this.crop_info)
                        ModuleService("demorunner","input_select_and_crop",url_params,
                                            this.RunDemo.bind(this)
                        ); // end input_select_and_crop
                    } else { // end if blobset
                        // upload files and run the demo
                        this.progress_info = "input upload";

                        // fill form data to upload
                        delete this.formData
                        this.formData = new FormData();
                        this.formData.append('demo_id',    this.ddl_json.demo_id);
                        this.formData.append('ddl_inputs', JSON.stringify(this.ddl_json.inputs));
                        var inputs  = this.ddl_json.inputs;
                        if (inputs.length===1) {
                            // Upload cropped image to server if the browser supports `HTMLCanvasElement.toBlob`
                            var crop_enabled = $("#id_cropinput").is(':checked');
                            if (crop_enabled) {
                                var cropped_canvas = $("#inputimage").cropper('getCroppedCanvas');
                                cropped_canvas.toBlob( 
                                    function(blob) {
                                        console.info('adding blob (cropped) : ', blob);
                                        this.formData.append('file_0', blob);
                                        this.UploadForm();
                                    }.bind(this), 'image/png' );
                            } else {
                                var image_src = $("#inputimage").attr('src');
                                blobUtil.imgSrcToBlob(image_src).then(
                                    function(blob) {
                                        this.formData.append('file_0', blob);
                                        this.UploadForm();
                                    }.bind(this), 'image/png' );
                            }
                        } else {
                            // if several input image, TODO: deal with crop of first image
                            var blobs_in_form=0;
                            for(var idx=0;idx<inputs.length;idx++) {
                                // TODO: deal with non-image data
                                // TODO: deal with optional data
                                var image_src = //$("#input_gallery").data("image_gallery").GetImage(idx)[0];
                                                    $('#localdata_preview_'+idx).attr("src");
                                blobUtil.imgSrcToBlob(image_src).then(
                                    function(idx,obj) { return function(blob) {
                                        console.info('idx=',idx);
                                        obj.formData.append('file_'+idx, blob);
                                        blobs_in_form++;
                                        console.info('blobs_in_form=',blobs_in_form);
                                        if(blobs_in_form==obj.ddl_json.inputs.length) {
                                            obj.UploadForm();
                                        }
                                    }
                                    }(idx,this), 'image/png' );
                            }
                        }

                    }
                }.bind(this)
                ); // end init_demo
            } // end if 
        }.bind(this)
        );
    }
    
};
