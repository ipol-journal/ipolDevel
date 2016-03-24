
// using strict mode: better compatibility
"use strict";



//------------------------------------------------------------------------------
// preprocess DDL demo, filling some properties:
//   input.max_pixels if string
//   input.max_weight if string
// default values for:
//   general.crop_maxsize
//   general.thumbnail_size
// set array of strings if single string for
//   general.input_description
//   general.param_description
// default value for 
//    params_layout
// 
function PreprocessDemo(demo) {
    //
    console.info("PreprocessDemo")
    console.info(demo)
    if (demo != undefined) {
        for (var input in demo.inputs) {
            // do some pre-processing
            if ($.type(input.max_pixels) === "string") {
                input.max_pixels = scope.$eval(input.max_pixels)
            }
            if ($.type(input.max_weight) === "string") {
                input.max_weight = scope.$eval(input.max_weight)
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
    if (demo.params_layout == undefined) {
        demo.params_layout = [
            ["Parameters:", range(demo.params.length)]
        ];
    }
};






//------------------------------------------------------------------------------
function OnDemoList(demolist)
{
    var dl = demolist;
    if (dl.status == "OK") {
        var str = JSON.stringify(dl.demo_list, undefined, 4);
        $("#tabs-demos pre").html(syntaxHighlight(str))
        console.info(dl);
    }

    // create a demo selection
    var html_selection = "<select>";
    for (var i=0; i<dl.demo_list.length; i++) {
        html_selection += '<option value = "'+i+'">'
        html_selection += dl.demo_list[i].editorsdemoid + 
                          '  '+ dl.demo_list[i].title
        html_selection += '</option>'
    }
    html_selection += "</select>";
    $("#demo-select").html(html_selection);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            InputController(dl.demo_list[pos].editorsdemoid,dl.demo_list[pos].id);
        });

};

//------------------------------------------------------------------------------
// List all demos and select one
//
function ListDemosController() {
    
    console.info("get demo list from server");
    var dl;

    ModuleService(
        'demoinfo',
        'demo_list',
        '',
        OnDemoList
    );
    
    
};




//------------------------------------------------------------------------------
// Starts everything needed for demo input tab
//
function InputController(demo_id,internal_demoid) {

    console.info("internal demo id = ", internal_demoid);
    if (internal_demoid > 0) {
        ModuleService(
            'demoinfo',
            'read_last_demodescription_from_demo',
            'demo_id=' + internal_demoid + '&returnjsons=True',
            function(demo_ddl) {
                console.info("read demo ddl status = ", demo_ddl.status);
                if (demo_ddl.status == "OK") {
                    var ddl_json = DeserializeJSON(demo_ddl.last_demodescription.json);
                    var str = JSON.stringify(ddl_json, undefined, 4);
                    $("#tabs-ddl pre").html(syntaxHighlight(str));
                }
                
                // hide crop
                $("#div_cropinput" ).hide();
                // empty inputs
                $("#DrawInputs").empty();
                
                PreprocessDemo(ddl_json);

                // Create local data selection to upload 
                CreateLocalData(ddl_json);

                // Create Parameters tab
                CreateParams(ddl_json);

                // Get demo blobs
                ModuleService(
                    "blobs",
                    "get_blobs_of_demo_by_name_ws",
                    "demo_name=" + demo_id,
                    OnDemoBlobs(ddl_json));
            });


    }
    

}
    
    
//------------------------------------------------------------------------------
// deals with the user blobs to upload
//
function CreateLocalData(ddl_json) {
    var html="";
    html += '<table style="margin-right:auto;margin-left:0px">';
    for(var i=0;i<ddl_json.inputs.length;i++) {
        html += '<tr>';
        html += '<td>';
          html += '<label for="file_'+i+'">'+ddl_json.inputs[i].description+'</label>';
        html += '</td>';
        html += '<td>';
          html += '<input type="file" name="file_'+i+'" id="file_'+i+'" size="40"';
          html += 'accept="'+ddl_json.inputs[i].ext+',image/*,media_type"';
          html += ' />';
        html += '</td>';
        html += '<td > <img id="localdata_preview_'+i+'" style="max-height:128px"></td>';
        html += '<td>';
        html += '<font size="-1"><i>';
          if (ddl_json.inputs[i].max_pixels!=undefined) {
            html += '<span>  &le;'+ddl_json.inputs[i].max_pixels+' pixels </span>';
          }
          if (ddl_json.inputs[i].max_weight!=undefined) {
            html += '<span> &le;'+ddl_json.inputs[i].max_weight/(1024*1024)+' Mb </span>';
          }
          if (ddl_json.inputs[i].required!=undefined && !ddl_json.inputs[i].required) {
            html += '<span> (optional) </span>';
          }
        html += '</i></font>';
        html += '</td>';
        html += '</tr>';
    }
    html += '</table>';
//     html += '<input type="submit" value="select" />';
    $("#local_data").html(html);
    
    // deal with events
    $( "#apply_localdata" ).click( (function(ddl_json) { return function(){
            // code to be executed on click
            var di = new DrawInputs(ddl_json);
            console.info("apply_local_data ", ddl_json);
            //di.SetBlobSet(this.demoblobs.blobs[event.data.blobset_id]);
            di.CreateHTML();
//             di.CreateCropper();
            di.LoadDataFromLocalFiles();
        }
    })(ddl_json));
    
    for(var i=0;i<ddl_json.inputs.length;i++) {
        $("#file_"+i).change( 
            (function(i) { return function() {

                console.info("files=",this.files);
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = (function(i) { return function (e) {
                        console.info("onload ", i, ":",e.target);
                        $('#localdata_preview_'+i).attr("src", e.target.result);
                    } })(i);
                    reader.readAsDataURL(this.files[0]);
                }
            } }) (i)
        );
    }
}
    

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



function DocumentReady() {

    $("#tabs").tabs({
            activate: function(event, ui) {
                var active = $('#tabs').tabs('option', 'active');
            }
        }

    );
    
    // get url parameters (found on http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript/21152762#21152762)
    var url_params = {};
    location.search.substr(1).split("&").forEach(function(item) {
        var s = item.split("="),
            k = s[0],
            v = s[1] && decodeURIComponent(s[1]);
        (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
    })
    
    console.info("url parameters = ",url_params);

    // Set cursor to pointer and add click function
    $("legend").css("cursor","pointer").click(function(){
        var legend = $(this);
        var value = $(this).children("span").html();
        if(value=="[-]")
            value="[+]";
        else
            value="[-]";
       $(this).siblings().slideToggle("slow", function() { legend.children("span").html(value); } );
    });
    
    
//     $.ajax({
//         crossOrigin: true,
//         url: "http://localhost:8000/test_input.html",
//         success: function(data) {
//             console.log(data);
//         }
//     });
        
//     $("#tabs-input").load("http://localhost:8000/test_input.html");
//     $("#tabs-params").load("http://localhost:8000/test_params.html");

    ListDemosController();
    var demo_id = 20;
    

}
$(document).ready(DocumentReady);