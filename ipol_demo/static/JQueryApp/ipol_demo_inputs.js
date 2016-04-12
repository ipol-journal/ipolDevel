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
            html += '<div class="gallery2" > ' +
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
                    images[idx].onload = (function(draw_info,idx_str) { 
                        return function () {
                            if (draw_info.display_ratio==-1) {
                                // compute display ratio
                                draw_info.display_ratio=(this.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/this.naturalWidth;
                                //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
                                console.info("width ", this.naturalWidth ," display_ratio ", draw_info.display_ratio);
                                $('.gallery2').attr("style", "height:"+(this.naturalHeight*draw_info.display_ratio+10+15)+'px;');
                            }
                            $('#inputimage_'+idx_str).attr("src", this.src);
                            $('#inputimage_'+idx_str).attr("height",(this.naturalHeight*draw_info.display_ratio)+'px');
                            $('#state_'+idx_str).html("");
        //                     $('#inputimage_'+idx).attr("height",(this.naturalHeight*draw_info.display_ratio)+'px');
                        };
                    })(this.draw_info,idx_str);
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
            image.onload = (function(draw_info,setcrop,crop_info) { 
                return function () {
                    // compute display ratio
                    draw_info.display_ratio=(this.naturalWidth < draw_info.maxdim)?1: draw_info.maxdim/this.naturalWidth;
                    //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
                    console.info("width ", this.naturalWidth ," display_ratio ", draw_info.display_ratio);
                    $('#inputimage').attr("src", this.src);
                    $('#inputimage_div').css ("height", (this.naturalHeight*draw_info.display_ratio)+'px');
                    $('#inputimage_div').css ("width",  (this.naturalWidth *draw_info.display_ratio)+'px');
                    $('#previewimage')  .css ("height", (this.naturalHeight*draw_info.display_ratio)+'px');
                    $('#inputimage')    .attr("height", (this.naturalHeight*draw_info.display_ratio)+'px');
                    $('#image_info').html(  Math.round(this.naturalWidth)+"x"+
                                            Math.round(this.naturalHeight)+
                                            " (x"+(draw_info.display_ratio).toFixed(2)+")");
                    setcrop();
                    crop_info.w = this.naturalWidth;
                    crop_info.h = this.naturalHeight;
                    console.info("crop_info = ", crop_info);
                    console.info("onload function end");
                };
            })(this.draw_info,this.SetCrop.bind(this),this.crop_info);
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
                var image = new Image();
                image.src =  $('#localdata_preview_'+idx).attr("src");
                if (this.draw_info.display_ratio==-1) {
                    // compute display ratio
                    this.draw_info.display_ratio=(image.naturalWidth < this.draw_info.maxdim)?1: this.draw_info.maxdim/image.naturalWidth;
                    //$(".gallery2").attr("height",(this.naturalHeight*draw_info.display_ratio+5)+'px');
                    console.info("width ", image.naturalWidth ," display_ratio ", this.draw_info.display_ratio);
                    $('.gallery2').attr("style", "height:"+(image.naturalHeight*this.draw_info.display_ratio+10+15)+'px;');
                }
                $('#inputimage_'+idx).attr("src",image.src);
                $('#inputimage_'+idx).attr("height",(image.naturalHeight*this.draw_info.display_ratio)+'px');
                $('#state_'+idx).html("");
                
                // several images, take crop info from first image
                if (idx==0) {
                    this.crop_info.x = 0;
                    this.crop_info.y = 0;
                    this.crop_info.w = image.naturalWidth;
                    this.crop_info.h = image.naturalHeight;
                }

            }
            console.info("crop_info = ", crop_info);
        } else {
            var image = new Image();
            image.src =  $('#localdata_preview_0').attr("src");
            // compute display ratio
            this.draw_info.display_ratio=(image.naturalWidth < this.draw_info.maxdim)?1: this.draw_info.maxdim/image.naturalWidth;
            $('#inputimage').attr("src", image.src);
            $('#inputimage_div').css ("height",(image.naturalHeight*this.draw_info.display_ratio)+'px');
            $('#inputimage_div').css ("width", (image.naturalWidth *this.draw_info.display_ratio)+'px');
            $('#previewimage')  .css ("height",(image.naturalHeight*this.draw_info.display_ratio)+'px');
            $('#inputimage')    .attr("height",(image.naturalHeight*this.draw_info.display_ratio)+'px');
            $('#image_info').html(  Math.round(image.naturalWidth)+"x"+
                                    Math.round(image.naturalHeight)+
                                    " (x"+(this.draw_info.display_ratio).toFixed(2)+")");
            this.SetCrop();
            this.crop_info.x = 0;
            this.crop_info.y = 0;
            this.crop_info.w = image.naturalWidth;
            this.crop_info.h = image.naturalHeight;
            console.info("crop_info = ", crop_info);
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
 
        this.progressbar.progressbar({
            value: 100,
            change: function() {
                var current_time = new Date().getTime();
                var elapsed = current_time-this.starttime;
                if (elapsed<2000) {
                    this.progresslabel.text( Math.round(elapsed/100)/10 + " sec." );
                } else {
                    this.progresslabel.text( Math.round(elapsed/1000) + " sec." );
                }
            }.bind(this),
            complete: function() {
                this.progresslabel.text( "Rerun" );
            }.bind(this)
        });
        
        console.info("progresslabel= ", this.progresslabel);
        this.progresslabel.text("Run");
    }
    
    //--------------------------------------------------------------------------
    this.progress = function( start=-1) {
        var val = this.progressbar.progressbar( "value" );
        if (start!=-1) {
            this.starttime = new Date().getTime();
            val=start;
        }
        this.progressbar.progressbar( "value", val + 1 );
        if ( val < 99 ) {
            var current_time = new Date().getTime();
            var elapsed = current_time-this.starttime;
            if (elapsed<2000) {
                setTimeout( this.progress.bind(this), 100 );
            } else {
                setTimeout( this.progress.bind(this), 1000 );
            }
        }
    }

    //--------------------------------------------------------------------------
    this.GetParamValue = function(index) {

        var name = this.ddl_json.params[index].id;
        
        switch(this.ddl_json.params[index].type) {
            case "selection_collapsed":
                var value = $("select[name="+name+"]").val();
                return value;
            case "selection_radio":
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
                break;
            case "checkboxes":
                break;
        }
        return undefined;
    }
    
    //--------------------------------------------------------------------------
    this.SetRunEvent = function() {

        this.InitProgress();
        this.progressbar.click( 
        function(){
            if ((this.progresslabel.text()==="Rerun")||
                (this.progresslabel.text()==="Run"  )) {

                // disable future clicks until run is finished
                this.progresslabel.text( "" );
                this.progress(0);
                // code to be executed on click
                DemoRunnerService("init_demo",
                                    "demo_id="+this.ddl_json.demo_id+
                                    "&ddl_build="+JSON.stringify(this.ddl_json.build),
                function(res) {
                    console.info("init_demo res=", res);
                    // select input from blobset or upload from local files
                    console.info("input_origin = ", this.input_origin);
                    if (this.input_origin==="blobset") {
                        // Set inputs using blobset
                        // crop at the same time
                        DemoRunnerService("input_select_and_crop",
                                        "demo_id="+this.ddl_json.demo_id+
                                        "&ddl_inputs="+JSON.stringify(this.ddl_json.inputs)+
                                        "&"+this.blobset[0].html_params+
                                        "&crop_info="+encodeURIComponent(JSON.stringify(this.crop_info)),
                        function(res) {
                            console.info("crop_info res=", res);
                            // create parameters
                            params={};
                            if (this.ddl_json.params) {
                                for(var p=0;p<this.ddl_json.params.length;p++) {
                                    var name = this.ddl_json.params[p].id;
                                    var value = this.GetParamValue(p);
                                    params[name] = value;
                                    console.info("param ",p," ",name, ":", value);
                                }
                            }
                            // add crop info as parameters (would only need image size...)
                            params['x0']=Math.round(this.crop_info.x);
                            params['x1']=Math.round(this.crop_info.x+this.crop_info.w);
                            params['y0']=Math.round(this.crop_info.y);
                            params['y1']=Math.round(this.crop_info.y+this.crop_info.h);
                            console.info("params = ",params);
                            // run demo
                            DemoRunnerService("run_demo",
                                            "demo_id="+this.ddl_json.demo_id+
                                            "&key="+res.key+
                                            "&ddl_run="+encodeURIComponent(JSON.stringify(this.ddl_json.run))
                                            +
                                            "&params=" +encodeURIComponent(JSON.stringify(params)),
                            function(res) {
                                // stop progress
                                this.progress(100);
                                console.info("run_demo res=", res);
                                var dr = new DrawResults(   res,
                                                            this.ddl_json.results );
                                dr.Create();
                            }.bind(this)
                            ).fail( function() { this.progress(100); } );
                                // end of run_demo
                        }.bind(this)
                        ); // end input_select_and_crop
                    }
                }.bind(this)
                ); // end init_demo
            } // end if
        }.bind(this)
        );
    }
    
};
