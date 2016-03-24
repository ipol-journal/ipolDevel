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
    
    this.ddl_json  = ddl_json;
    this.draw_info = { maxdim:768,  display_ratio:-1};

    //--------------------------------------------------------------------------
    this.SetBlobSet = function(blobset) {
        this.blobset = blobset;
    }
    
    
    //--------------------------------------------------------------------------
    this.BlobHasImage = function( blob_idx) {
        var image_found = false;
        var blobset = this.blobset;
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
        
        var html = "";
        var inputs = this.ddl_json.inputs;
        
        // use gallery only if several images 
        if (inputs.length>1) {
            html += '<div class="gallery2" > ' +
                    '<ul class="index1"> ';
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
                        '<td><div id="inputimage_div" style="float:left;margin:5px;">'+
                            '<img  id="inputimage" crossOrigin="Anonymous"'+
                                //'style="padding:5px;'+
                                'max-width:' +this.draw_info.maxdim+'px;'+
                                'max-height:'+this.draw_info.maxdim+'px;'+
                                'width:auto;height:auto;float:left"' +
                            '>'+
                        '</div></td>'+
                        '<td class="table_crop">'+
                            '<div id="previewimage" style="height:500px;float:left;margin:5px">'+
                                '<div class="preview"></div>'+
                            '</div>'+
                        '</td>'+
                    '</tr>'+
                    '<tr>'+
                        '<td id="image_info" style="text-align:center;"></td>'+
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
            image.onload = (function(draw_info,setcrop) { 
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
                };
            })(this.draw_info,this.SetCrop.bind(this));
            image.src = blobs_url+blob;
        }
    };
    
    //--------------------------------------------------------------------------
    this.LoadDataFromLocalFiles = function() {
        var inputs  = this.ddl_json.inputs;
        var blobset = this.blobset;
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
            }
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
                    // adapted preview code from example customize-preview.html
                    build: function (e) {
                        var $clone = $(this).clone();

                        $clone.css({
                        display: 'block',
                        width: '100%',
                        minWidth: 0,
                        minHeight: 0,
                        maxWidth: 'none',
                        maxHeight: 'none'
                        });

                        var $previews = $('.preview');
                        $previews.css({
                        height: '100%',
                        overflow: 'hidden'
                        }).html($clone);
                    },

                    crop: function (e) {
                        var imageData = $(this).cropper('getImageData');
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
                        });
                    }
                });
            }
//             $('#inputimage_table td:nth-child(2)').show();
            $('.table_crop').show();
            
        } else {
            $("#div_cropinput" ).hide();
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
        var inputs  = this.ddl_json.inputs;
        if (inputs.length===1) {
            $("#div_cropinput" ).show();
            $("#id_cropinput").change( function() { this.SetCrop(); }.bind(this));
            var crop_enabled = $("#id_cropinput").is(':checked');
            //console.info("SetCrop ",  crop_enabled);
            if (crop_enabled) {
                this.CreateCropper();
            } else {
                this.DestroyCropper();
            }
        }
    }
    
};
