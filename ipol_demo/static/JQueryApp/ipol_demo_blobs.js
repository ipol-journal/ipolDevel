//
// IPOL demo system
// CMLA ENS Cachan
// 
// file: ipol_demo_blobs.js
// date: march 2016
// author: Karl Krissian
//
// description:
// this file contains the code that renders and deals with the demo blobs
// associated with ipol_demo.html and ipol_demo.js
//

"use strict";

//------------------------------------------------------------------------------
var BlobsContainer = function(demoblobs, ddl_json)
{

    console.info("constructor : ", demoblobs);
    this.demoblobs = demoblobs;
    this.ddl_json  = ddl_json;
    console.info("this.demoblobs : ", this.demoblobs);

        
    //--------------------------------------------------------------------------
    this.append_blobs = function(db) {
        console.info("append_blobs ", this.demoblobs, " -- ", db);
        this.demoblobs.blobs = this.demoblobs.blobs.concat(db.blobs);
        this.UpdateDemoBlobs();
    }

    //--------------------------------------------------------------------------
    this.UpdateDemoBlobs = function() {

        console.info("demoblobs.blobs.length=",this.demoblobs.blobs.length);
        
        var str = JSON.stringify(this.demoblobs, undefined, 4);
        $("#tabs-blobs pre").html(syntaxHighlight(str));

        this.PreprocessDemo();
        this.DrawDemoBlobs();
        
        $("#ThumbnailSize")      .change( function() { this.DrawDemoBlobs(); }.bind(this));
        $("#ShowCreditsCheckbox").change( function() { this.DrawDemoBlobs(); }.bind(this));
        $("#ShowTitlesCheckbox") .change( function() { this.DrawDemoBlobs(); }.bind(this));
    }
        
    //--------------------------------------------------------------------------
    this.PreprocessDemo = function() {
        
        var blobs = this.demoblobs.blobs;
        
        // preprocess HTML parameters string
        // for each blob set, in the form
        // html_params="url=XXXX&0:blob&1:blob&2:blob,blob etc ..."
        for(var i=0;i<blobs.length;i++)
        {
            var blobset = blobs[i];
            blobset[0].html_params = "url=" + this.demoblobs.url + "&"
                // extract only contents of interest
            var blobset_contents = blobset.slice(1);
            blobset_contents.sort(function(a, b) {
                return (a.id_in_set < b.id_in_set ? -1 : (a.id_in_set > b.id_in_set ? 1 : 0));
            });
            var current_id = ""
            for (var idx = 0; idx < blobset_contents.length; idx++) {
                if (idx == 0) {
                    blobset[0].html_params += blobset_contents[idx].id_in_set + ":";
                } else {
                    // if same id, separate by comma ...
                    if (blobset_contents[idx].id_in_set == current_id) {
                        blobset[0].html_params += ",";
                    } else {
                        // else separate arguments
                        blobset[0].html_params += "&" + blobset_contents[idx].id_in_set + ":";
                    }
                }
                current_id = blobset_contents[idx].id_in_set;
                blobset[0].html_params += blobset_contents[idx].hash +
                    blobset_contents[idx].extension;
            }
        }
        
    }

    //--------------------------------------------------------------------------
    this.DrawDemoBlobs = function() {
        $("#displayblobs").html(this.CreateBlobSetDisplay());
        this.DemoBlobsEvents();
    }
    
    //--------------------------------------------------------------------------
    this.CreateBlobSetDisplay = function()
    {
        var blobsets_html = "";
        
        var thumbnail_size   = $("#ThumbnailSize option:selected").text();
        var display_credits  = $("#ShowCreditsCheckbox").is(':checked');
        var display_titles   = $("#ShowTitlesCheckbox").is(':checked');
        
        console.info("ThumbailSize is  ",$("#ThumbnailSize option:selected").text());
        
        // loop over blobsets
        for(var i=0;i<this.demoblobs.blobs.length;i++)
        {
            var blobset = this.demoblobs.blobs[i];
            // represent the blob set within a HTML table
            var blobset_html = "";
            blobset_html += '<div  ';
            // set div id for click selection
            blobset_html += ' id="blobset_'+i+'"'
                         +  ' style="display:inline-block;vertical-align: top;">'
                         +  "<table  "+'id="table_blobset_'+i+'"'
                         +  "style='background-color:#EEEEEE;margin:3px;text-align:center;border=1px'>"
                         +  "<tr>";
            for(var idx=1;idx<blobset[0].size+1;idx++)
            {
                // blob display could be disabled ...
                blobset_html += "<td style='margin:0px;padding:0px;' id='blob_"+i+"_"+idx+"'>"
                // apply the selection ???

                blobset_html += '<div'
                             +  '  class="select_input"'
                             +  '  style="margin:0px;padding:2px;float:left;'
    //                          +  '         width:'       +thumbnail_size+'px;'
                             +  '         height:'      +thumbnail_size+'px;'
                             +  '         line-height:' +thumbnail_size+'px;'
                             +  '         text-align:center" > '
                // needed to add at least one character (here &nbsp;) to get it vertically centered on chrome ... !!!
                             +  '&nbsp;<img'
                             +  '   style=" max-width:'  +(thumbnail_size-6)+'px;'
                             +  '           max-height:' +(thumbnail_size-6)+'px;'
                             +  '           vertical-align:middle; margin:3px"'
                             +  '   src="'+this.demoblobs.url_thumb+
                                    '/thumbnail_'+blobset[idx].hash+blobset[idx].extension+'" '
                             +  '   alt='   +blobset[idx].title
                             +  '   title="'+blobset[idx].title+
                                    ' (credits: '+blobset[idx].credit+
                                    ', tags:'+blobset[idx].tag+')" >&nbsp;'
                             +  "</div> "
                             +  "</td>";
            }
            blobset_html += "</tr>";
            if (display_titles||display_credits) {
                blobset_html += '<tr  style="background-color:#EEEEEE;">';
                blobset_html += '<th colspan="'+blobset[0].size+'" ';
                blobset_html +=   'style="max-width:'+(blobset[0].size*thumbnail_size)+'px;font-weight:normal;" >';
                //          We could use the blob name but in general each image has the same title
                //             which is a better name <span>{{blob_set[0].set_name}}</span>
                if (display_titles) {
                    blobset_html += blobset[1].title;
                }
                if (display_credits) {
                    if (display_titles) {
                        blobset_html += '<br/>';
                    }
                    blobset_html += '<font size="-2"><i> <pre> &copy; '+blobset[1].credit+' </pre></i></font>';
                }
                blobset_html += "</th>";
                blobset_html += "</tr>";
            }
            blobset_html += "</table>";
            blobset_html += '</div>';
            blobsets_html += blobset_html;
        }
        
        return blobsets_html;
    }

    
    //--------------------------------------------------------------------------
    this.DemoBlobsEvents = function() {
        var blobs = this.demoblobs.blobs;
        // set click events on blobsets
        for(var i=0;i<blobs.length;i++) {
            $("#blobset_"+i).click( {blobset_id: i}, function(event) {
                var di = new DrawInputs(this.ddl_json);
                di.SetBlobSet(this.demoblobs.blobs[event.data.blobset_id]);
                di.input_origin = "blobset";
                di.CreateHTML();
//                 di.CreateCropper();
                di.LoadDataFromBlobSet();
                //console.info("blobset "+event.data.blobset_id+" clicked ");
                di.SetRunEvent();
            }.bind(this)
            );

            
            $("#table_blobset_"+i).hover(
                (function(id) {
                    return function() {
                       $("#table_blobset_"+id+" tr div").css('background-color','#CD5555');
                    };
                })(i),
                (function(id) {
                    return function() {
                        $("#table_blobset_"+id+" tr div").css('background-color','#EEEEEE');
                    };
                })(i)
            );

            var blobset = this.demoblobs.blobs[i];
            this.max_ratio = 0.5; 
            for(var idx=1;idx<blobset[0].size+1;idx++)
            {
                // check if thumbnail load works, if not, hide the corresponding
                // image
                var tester=new Image();
                tester.onerror=(function(i,idx) { return function() {
                    $("#blob_"+i+"_"+idx).html("");
                }; })(i,idx);
                tester.src=this.demoblobs.url_thumb+'/thumbnail_'+blobset[idx].hash+blobset[idx].extension;
                tester.onload = function(obj) { return function() {
                    // Run onload code.
                    // set lowest possible height for all thumbnails
                    var prev_ratio = obj.max_ratio;
                    obj.max_ratio = Math.min(Math.max(obj.max_ratio,this.height/this.width),1);
                    if (prev_ratio!=obj.max_ratio) {
                        var thumbnail_size   = $("#ThumbnailSize option:selected").text();
                        var new_height = thumbnail_size*obj.max_ratio;
                        $(".select_input").css({'height'      :new_height+'px',               
                                                'line-height' :new_height+'px'});
                    }
                }; }(this);
            } 

            
        }
        
    }
};

//------------------------------------------------------------------------------
// function called when receiving the list of demo blobs for user selection
function OnDemoBlobs(ddl_json) {
    return function (demoblobs) {
        
        console.info("*** demoblobs");
        console.info("demoblobs=",demoblobs);
        console.info("ddl_json=",ddl_json);
        
        if (demoblobs.status=="KO") {
            return;
        }
        
        var bc = new BlobsContainer(demoblobs, ddl_json);
        
        // Check for template
        if (demoblobs.use_template.hasOwnProperty('name')) {
            // get template blobs
            var template_name = demoblobs.use_template.name;
            console.info("getting template ***")
            ModuleService(
                "blobs",
                "get_blobs_from_template_ws",
                "template="+template_name,
                function(db){bc.append_blobs(db)}
            );
        } else {
            bc.UpdateDemoBlobs();
        }
        
    }
}
