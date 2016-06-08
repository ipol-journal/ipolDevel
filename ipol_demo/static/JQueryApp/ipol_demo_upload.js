//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_upload.js
// date: june 2016
// author: Karl Krissian
//
// description:
// upload from local data
//

// using strict mode: better compatibility
"use strict";

// for browser history features, save last uploaded files locally
var last_uploaded_files = [];
// use windows.localStorage to avoid displaying a wrong input 
// (position will be unique for each upload, even after page refresh)
var last_uploaded_files_pos = window.localStorage.getItem("last_uploaded_files_pos");
if (!last_uploaded_files_pos) {
    last_uploaded_files_pos = 0;
    window.localStorage.setItem("last_uploaded_files_pos", last_uploaded_files_pos);
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
        html += '<td > <img crossorigin="anonymous"  id="localdata_preview_'+i+'" style="max-height:128px"></td>';
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
    //html += '<input type="submit" value="select" />';
    $("#local_data").html(html);
    
//     // deal with events
//     $( "#apply_localdata" ).click( (function(ddl_json) { return function(){
//             // code to be executed on click
//             var di = new DrawInputs(ddl_json);
//             console.info("apply_local_data ", ddl_json);
//             di.SetBlobSet(null);
//             di.CreateHTML();
//             //di.CreateCropper();
//             di.LoadDataFromLocalFiles();
//             di.SetRunEvent();
//         }
//     })(ddl_json));
    
    $("#upload-dialog").dialog("option","buttons",{
        Apply: (function(ddl_json) { 
            return function(){
                // empty results
                $("#ResultsDisplay").empty();
                $("#ResultsDisplay").removeData();
                // code to be executed on click
                var di = new DrawInputs(ddl_json);
                console.info("apply_local_data ", ddl_json);
                di.SetBlobSet(null);
                di.CreateHTML();
                //di.CreateCropper();
                di.LoadDataFromLocalFiles();
                di.SetRunEvent();
                $(this).dialog( "close" );
            }
        })(ddl_json),
        Cancel: function() {
          $(this).dialog( "close" );
        }
      });
    
    
    for(var i=0;i<ddl_json.inputs.length;i++) {
        $("#file_"+i).change( 
            (function(i) { return function() {

                console.info("files=",this.files);
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
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = (function(i) { return function (e) {
                        console.info("onload ", i, ":",e.target);
                        $('#localdata_preview_'+i).attr("src", e.target.result);
                        console.info("size of uploaded file :", e.target.result.length/1024/1024, " Mb" );
                        last_uploaded_files[last_uploaded_files_pos] = e.target.result;
                        $('#localdata_preview_'+i).data("src_pos",last_uploaded_files_pos);
                        last_uploaded_files_pos++;
                        window.localStorage.setItem("last_uploaded_files_pos", last_uploaded_files_pos);
                        // avoid filling the memory by release old files
                        if (last_uploaded_files_pos>=10) {
                            last_uploaded_files[last_uploaded_files_pos-10]=undefined;
                        }
                        
                    } })(i);
                    reader.readAsDataURL(this.files[0]);
                }
            } }) (i)
        );
    }
}
    
