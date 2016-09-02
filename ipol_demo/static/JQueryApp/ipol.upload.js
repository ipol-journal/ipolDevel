/**
 * @file 
 * Upload blobs from local data
 * @author  Karl Krissian
 * @version 0.1
 */

// using strict mode: better compatibility
"use strict";

// Image Processing OnLine (IPOL) journal demo system namespace
// @namespace
var ipol = ipol || {};

/**
 * upload features
 * @namespace
 */
ipol.upload = ipol.upload || {};


/**
 * for browser history features, save last uploaded files locally
 * @member {object[]} last_uploaded_files containing the information of the last uploaded files
 * @memberof ipol.upload
 */
ipol.upload.last_uploaded_files = [];

/**
 * use windows.localStorage to avoid displaying a wrong input 
 * (position will be unique for each upload, even after page refresh)
 * for browser history features, save last uploaded files locally
 * @member {number} last_uploaded_files_pos position within the array 
 * last_uploaded_files of the last uploaded files 
 * @defaults 0
 * @memberof ipol.upload
 */
ipol.upload.last_uploaded_files_pos = window.localStorage.getItem("last_uploaded_files_pos");
if (!ipol.upload.last_uploaded_files_pos) {
    ipol.upload.last_uploaded_files_pos = 0;
    window.localStorage.setItem("last_uploaded_files_pos", 
                                ipol.upload.last_uploaded_files_pos);
}
    

/**
 * Creates the HTML code to display
 * the local blobs to upload in the upload modal window,
 * set the HTML to the 'local_data' element (div)
 * @param {object} ddl_json demo description object
 */
ipol.upload.CreateUploadHTML = function(ddl_json) {
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
        html += '<td > <img crossorigin="anonymous"  id="localdata_preview_'+i+
                '" style="max-height:128px"></td>';
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
    $("#local_data").html(html);
}
    
/**
 * Creates and executes the events of choosing upload data
 * @param {object} ddl_json demo description object
 */
ipol.upload.UploadBlobsEvents = function(ddl_json) {
    for(var i=0;i<ddl_json.inputs.length;i++) {
        $("#file_"+i).change( 
            (function(i) { return function() {
                // check upload size
                var size_ok = this.files[0].size<eval(ddl_json.inputs[i].max_weight);
                var Mb=1024*1024;
                var file_size     = this.files[0].size/Mb;
                var allowed_size  = eval(ddl_json.inputs[i].max_weight)/Mb;
                console.info(" size ok = ", file_size.toPrecision(5), "<", 
                             allowed_size.toPrecision(5));
                if (!size_ok) {
                    alert("The selected file exceeds the maximal allowed size: "+ 
                            file_size.toPrecision(4)+" Mb >"+
                            allowed_size.toPrecision(4)+" Mb");
                    return;
                }
                
                // read the file, update the preview and the 
                // last_uploaded_files information
                if (this.files && this.files[0]) {
                    // use FileReader()
                    var reader = new FileReader();
                    reader.onload = (function(i) { return function (e) {
                        console.info("onload ", i, ":",e.target);
                        $('#localdata_preview_'+i).attr("src", e.target.result);
                        console.info("size of uploaded file :", 
                                     e.target.result.length/1024/1024, " Mb" );
                        // for browser history purposes:
                        // save the result in the last_upload_files array
                        // at position last_uploaded_files_pos
                        ipol.upload.last_uploaded_files
                            [ipol.upload.last_uploaded_files_pos] = e.target.result;
                        // stores the position in the HTML element
                        // this prevents uploading twice the save file while moving 
                        // in the browser history
                        $('#localdata_preview_'+i).data("src_pos",
                                                        ipol.upload.last_uploaded_files_pos);
                        // increment the position
                        ipol.upload.last_uploaded_files_pos++;
                        window.localStorage.setItem("last_uploaded_files_pos", 
                                                    ipol.upload.last_uploaded_files_pos);
                        // avoid filling the memory by releasing old files
                        // we try to keep the 10 last files 
                        // (depending on the available cache)
                        if (ipol.upload.last_uploaded_files_pos>=10) {
                            ipol.upload.last_uploaded_files
                                [ipol.upload.last_uploaded_files_pos-10]=undefined;
                        }
                        
                    } })(i);
                    reader.readAsDataURL(this.files[0]);
                }
            } }) (i)
        );
    }
}
    
/**
 * Deals with the user blobs to upload: creates the HTML code to display
 * the local blobs to upload in the upload modal window, set the
 * Apply and Cancel button events. Deals with the user input blob selection.
 * @param {object} ddl_json demo description object
 * @fires Apply button
 * @fires Cancel button
 * @inner
 */
ipol.upload.ManageLocalData = function(ddl_json) {
    
    ipol.upload.CreateUploadHTML(ddl_json);
    $("#upload-dialog").dialog("option","buttons",{
        Apply: (function(ddl_json) { 
            return function(){
                // empty results
                $("#ResultsDisplay").empty();
                $("#ResultsDisplay").removeData();
                // create DrawInputs instance
                var di = new ipol.DrawInputs(ddl_json);
                di.setBlobSet(null);
                di.createHTML();
                // enable loading data from local files
                di.loadDataFromLocalFiles();
                // create RunDemo instance
                var run = new ipol.RunDemo(ddl_json,
                                           di.getInputOrigin(),
                                           di.getCropInfo(),
                                           di.getBlobSet(), 
                                           di.getDrawFeature()
                                          );
                run.setRunEvent();
                $(this).dialog( "close" );
            }
        })(ddl_json),
        Cancel: function() {
          $(this).dialog( "close" );
        }
    });
    
    ipol.upload.UploadBlobsEvents(ddl_json);
}
    
