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
    
    this.ddl_json      = ddl_json;
    this.draw_info     = { maxdim:768,  display_ratio:-1};
    this.input_origin  = "";
    this.crop_info     = { enabled:false, x:0,y:0,w:1,h:1};
    this.progressbar   = $("#progressbar");
    this.progresslabel = $(".progress-label");
    
    //--------------------------------------------------------------------------
    this.SetBlobSet = function(blobset) {
        this.blobset = blobset;
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
            console.info("blob_links = ", blob_links);
            for(var bid=1;bid<blob_links.length;bid++) {
                console.info(" blob_idx = ", blob_idx, " ",parseInt(blob_links[bid].split(':')[0]));
                if ((parseInt(blob_links[bid].split(':')[0])===blob_idx) &&
                    (blob_links[bid].split(':')[1].toLowerCase().indexOf(".png")>-1) ) {
                    image_found = true;
                    console.info("image found");
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
            html += '<div class="gallery2" id="input_gallery"> ' +
                    '<ul class="index"> ';
            for(var idx=0;idx<inputs.length;idx++) {
                // search image with png extension at position idx+1
                var image_found = this.BlobHasImage(idx);
                // for the moment accept image type or .png files only
                if ((inputs[idx].type==='image')|| image_found) {
                    html +=
                        '<li><a href="#">' +
                        '<span>'+inputs[idx].description+
                                '<span id="state_'+idx+'"> (loading) </span>'+
                        '</span>'+
                        //'<span ng-if="demo.inputs[idx].status!='loaded'"> (loading) </span>'+
                        '<div class="galim">'+
                        '    <img  id="inputimage_'+idx+'"'+
                        '        crossOrigin="Anonymous"'+
                        '        style=padding:5px,'+
                        '              max-width:' +this.draw_info.maxdim+'px,'+
                        '              max-height:'+this.draw_info.maxdim+'px,'+
                        '              width:auto,height:auto"'+
    //                     '        styleParent'+
    //                     '        imageonfail="DisableImage(demo.inputs[idx])"'+
    //                     '        imageonload="LoadedImage (demo.inputs[idx])"'+
                        '        />'+
                        '<br/><span id="inputinfo_'+idx+'"> image info </span>'+
                        '</div>'+
                        '</a></li>';
                } else {
                }
            }
            html += '</ul>' +
                    '</div>';
            
        } else {
            // simple image output
            html += '<div style="clear:both"> </div>'+
                    '<table id="inputimage_table">'+
                    '<tr>'+
                        '<td><div id="inputimage_div" style="float:left;margin:0px;">'+
                            '<img  id="inputimage" crossOrigin="Anonymous"'+
                                //'style="padding:5px;'+
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
                            '<td style="border:0;width:5em;margin:0;padding:0;">'+
                                '<input id="id_cropinput" type="checkbox" >crop'+
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
    // on load one of multiple input images
    //   - idx_str input index as a string
    //   - array of images being loaded
    //   - current loaded image
    this.OnLoadImageFromMultiple = function(idx_str,images,image) { 
        var draw_info = this.draw_info;
        var crop_info = this.crop_info;
        var current_ratio = this.draw_info.maxdim/image.naturalWidth;
        if ((draw_info.display_ratio==-1)||
            (current_ratio<this.draw_info.display_ratio)) {
            // compute display ratio
            draw_info.display_ratio=(image.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/image.naturalWidth;
            console.info("width ", image.naturalWidth ," display_ratio ", draw_info.display_ratio);
            $('#input_gallery').attr("style", "height:"+(image.naturalHeight*draw_info.display_ratio+10+15)+'px;');
        }
        $('#inputimage_'+idx_str).attr("src", image.src);
        $('#state_'+idx_str).html("");
        // set height for all images
        for(var idx=0;idx<this.ddl_json.inputs.length;idx++) {
            if (this.IsImageOk(images[idx])) {
                console.info(idx_str," setting input_image ",idx," height ",(images[idx].naturalHeight*draw_info.display_ratio));
                $('#inputimage_'+idx).css("height",(images[idx].naturalHeight*draw_info.display_ratio)+'px');
                $('#inputinfo_'+idx).html(
                    Math.round(images[idx].naturalWidth)+"x"+
                    Math.round(images[idx].naturalHeight)+
                    " (x"+(draw_info.display_ratio).toFixed(2)+")");
            }
        }
        // several images, take crop info from first image
        if (idx_str=='0') {
            crop_info.x = 0;
            crop_info.y = 0;
            crop_info.w = image.naturalWidth;
            crop_info.h = image.naturalHeight;
        }
    };
 
        
    //--------------------------------------------------------------------------
    // on load a single input image
    this.OnLoadSingleImage = function(image) { 
        var draw_info = this.draw_info;
        var crop_info = this.crop_info;
        // compute display ratio
        draw_info.display_ratio=(image.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/image.naturalWidth;
        //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
        console.info("width ", image.naturalWidth ," display_ratio ", draw_info.display_ratio);
        $('#inputimage').attr("src", image.src);
        $('#inputimage_div').css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage_div').css ("width",  (image.naturalWidth *draw_info.display_ratio)+'px');
        $('#previewimage')  .css ("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#inputimage')    .attr("height", (image.naturalHeight*draw_info.display_ratio)+'px');
        $('#image_info').html(  Math.round(image.naturalWidth)+"x"+
                                Math.round(image.naturalHeight)+
                                " (x"+(draw_info.display_ratio).toFixed(2)+")");
        this.SetCrop();
        crop_info.x = 0;
        crop_info.y = 0;
        crop_info.w = image.naturalWidth;
        crop_info.h = image.naturalHeight;
        console.info("crop_info = ", crop_info);
        console.info("onload function end");
    }
    
    
    //--------------------------------------------------------------------------
    this.LoadDataFromBlobSet = function() {

        
        var inputs  = this.ddl_json.inputs;
        var blobset = this.blobset;
        this.input_origin = "blobset";

        // load input image ...
        var blobs_url_params = blobset[0].html_params.split('&');
        console.info("blobs_url_params=",blobs_url_params);
        var blobs_url = blobs_url_params[0].split('=')[1];
        
        if (inputs.length>1) {
            var images = new Array(inputs.length);
            for(var idx=0;idx<inputs.length;idx++) {
                if (idx+1<blobs_url_params.length) {
                    var idx_str = blobs_url_params[idx+1].split(':')[0];
                    var blob    = blobs_url_params[idx+1].split(':')[1];
                    images[idx] = new Image();
                    images[idx].onload = (function(drawinputs,idx_str,images) { 
                        return function () {
                            drawinputs.OnLoadImageFromMultiple(idx_str,images,this);
                        };
                    })(this,idx_str,images);
                    // if non image type, seach for a png in the file list
                    if (blob.indexOf(',')>-1) {
                        var blobs = blob.split(',');
                        for(var n=0;n<blobs.length;n++) {
                            if (blobs[n].toLowerCase().endsWith(".png")) {
                                blob = blobs[n];
                            }
                        }
                    }
                    console.info(" blob link is ", blobs_url+blob);
                    images[idx].src = blobs_url+blob;
                }
            }
            // we don't deal with crop with multiple inputs for the moment
//             this.CreateCropper();
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
        console.info("LoadDataFromBlobSet end");
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
                this.OnLoadImageFromMultiple(idx.toString(),images,images[idx]);

            }
            console.info("crop_info = ", this.crop_info);
        } else {
            var image = new Image();
            image.src =  $('#localdata_preview_0').attr("src");
            this.OnLoadSingleImage(image);
        }
    };
    

    //--------------------------------------------------------------------------
    this.CreateCropper = function() {
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

                    cropend: function(ddl_json) {
                        return function (e) {
                            // update parameters in case they depend on the crop
                            UpdateParams(ddl_json);
                        }
                    } (this.ddl_json),
                                         

                    crop: function(crop_info, ddl_json) {
                        return function (e) {
                            var imageData  = $(this).cropper('getImageData');
                            var canvasData = $(this).cropper('getCanvasData');
                            var ratio = imageData.width / imageData.naturalWidth;
                            
//                             console.info("*** ratio = ", ratio);
                            
                            if (ddl_json.general.hasOwnProperty('crop_maxsize_new')) {
                                var maxdim = eval(ddl_json.general.crop_maxsize_new);
                                console.info("maxdim = ",maxdim);
                            }
                            var resize=false;
                            if (Math.round(e.width)>maxdim) {
                                console.info("e.width = ", e.width);
                                e.width = maxdim;
                                resize=true;
                            }
                            if (Math.round(e.height)>maxdim) {
                                console.info("e.height = ", e.height);
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

                                $("#crop_info").html(Math.round(e.width)+"x"+Math.round(e.height)+" (x"+(1/imageScaledRatio).toFixed(2)+")");
                                
                                $preview.width(previewWidth).find('img').css({
                                    width: imageData.naturalWidth / imageScaledRatio,
                                    height: imageData.naturalHeight / imageScaledRatio,
                                    marginLeft: -e.x / imageScaledRatio,
                                    marginTop: -e.y / imageScaledRatio
                                });
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
            $('.table_crop').show();
            
        } else {
//             $('#inputimage_table td:nth-child(2)').hide();
            $('.table_crop').hide();
        }
    }
    
    //--------------------------------------------------------------------------
    this.DestroyCropper = function() {
        $("#inputimage").cropper('destroy');
//         $('#inputimage_table td:nth-child(2)').hide();
        $('.table_crop').hide();
    }
    
    //--------------------------------------------------------------------------
    this.SetCrop = function() {
//         console.info("SetCrop begin");
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            $("#id_cropinput").change( function() { this.SetCrop(); }.bind(this));
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
            this.crop_info.w = $('#inputimage_0').naturalWidth();
            this.crop_info.h = $('#inputimage_0').naturalHeight();
        }
//         console.info("SetCrop end");
        console.info("cropinfo = ",this.crop_info);
    }
    
    
    //--------------------------------------------------------------------------
    this.InitProgress = function() {

        console.info("InitProgress");
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
        
        console.info("progresslabel= ", this.progresslabel);
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
    this.GetParamValue = function(index) {

        var param = this.ddl_json.params[index];
        var name  = param.id;
        
        switch(param.type) {
            case "selection_collapsed":
                var value = $("select[name="+name+"]").val();
                return value;
            case "selection_radio":
                var value = $("input[name="+name+"]:checked").val();
                return value;
                break;
            case "range":
                var value = $("input[name="+name+"]").val();
                return parseFloat(value);
            case "range_scientific":
                var value = $("input[name="+name+"]").val();
                return parseFloat(value);
            case "readonly":
                var value = $("input[name="+name+"]").val();
                return value;
            case "label":
                break;
            case "checkbox":
                var value = $("input[name="+name+"]").is(':checked');
                return value;
            case "checkboxes":
                var values = [];
                for (var n=0;n< param.values.length; n++) {
                    var group = param.values[n];
                    for (var id in group) {
                        if ($("input[name="+param.id+'_'+id+"]").is(':checked')) {
                            values.push(id);
                        }
                    }
                }
                console.info("values",values);
                return values;
        }
        return undefined;
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
        console.info("upload/select&crop res=", res);
        if (res.status==="KO") {
            this.progress_info = "upload/select&crop:failure";
            this.progress(100);
            return;
        } else {
            // reset progress after build
            //this.progress(0);
        }
        // create parameters
        var params={};
        if (this.ddl_json.params) {
            for(var p=0;p<this.ddl_json.params.length;p++) {
                var name = this.ddl_json.params[p].id;
                var value = this.GetParamValue(p);
                if (this.ddl_json.params[p].type==="checkbox") {
                    // set both ...
                    params[name+"_checked"] = value;
                    params[name] = value;
                } else {
                    if (this.ddl_json.params[p].type==="checkboxes") {
                        $.each( value, 
                                    function(index,param) {
                                        params[name+'_'+param]=true;
                                    }
                                );
                    } else {
                        params[name] = value;
                    }
                }
                console.info("param ",p," ",name, ":", value);
            }
        }
        // add crop info as parameters (would only need image size...)
        params['x0']=Math.round(this.crop_info.x);
        params['x1']=Math.round(this.crop_info.x+this.crop_info.w);
        params['y0']=Math.round(this.crop_info.y);
        params['y1']=Math.round(this.crop_info.y+this.crop_info.h);
        console.info("params = ",params);
        // create meta information
        var meta={};
        meta["max_width"]  = res["max_width"];
        meta["max_height"] = res["max_height"];
        
        this.progress_info = "run_demo";
        // run demo
        var url_params = "demo_id="+this.ddl_json.demo_id+
                    "&key="+res.key+
                    "&ddl_run="+this.json2uri(this.ddl_json.run)+
                    "&params=" +this.json2uri(params)+
                    "&meta=" +this.json2uri(meta);
        if (this.ddl_json['config']) {
            url_params += "&ddl_config="+this.json2uri(this.ddl_json.config)
        }
        DemoRunnerService("run_demo",url_params,
            function(res) {
                if (res.status==="KO") {
                    console.info("demo run res:",res);
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
                console.info("run_demo res=", res);
                var dr = new DrawResults( res, this.ddl_json.results );
                dr.Create();
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
                DemoRunnerService("init_demo", url_params,
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
                        DemoRunnerService("input_select_and_crop",url_params,
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
                                var image_src = $("#inputimage_"+idx).attr('src');
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
