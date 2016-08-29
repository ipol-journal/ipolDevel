/**
 * @file 
 * this file contains the code that renders and deals with the demo blobs
 * associated with ipol_demo.html and ipol_demo.js
 * @author  Karl Krissian
 * @version 0.1
 */


"use strict";


// ipol application namespace
var ipol = ipol || {};

//------------------------------------------------------------------------------
/**
 * Display proposed demo blobs
 * @constructor
 * @param demoblobs {object} object containing the list of demo blobs
 * @param ddl_json  {object} DDL description of the demo
 */
ipol.DrawBlobs = function(demoblobs, ddl_json)
{

    /** 
     * By convention, we create a private variable '_this' to
     * make the object available to the private methods.
     * @var {object} _this
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _this = this;

    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function _infoMessage
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ipol.DrawBlobs ----");
            console.info.apply(console,args);
        }
    }
    
    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} _verbose
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _verbose=true;
    _infoMessage(" ipol.DrawBlobs started ");
    _verbose=false;
    
    /** 
     * list of demo blobs.
     * @var {object} _demoblobs
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _demoblobs = demoblobs;
    
    /** 
     * Demo Description Language DDL information.
     * @var {object} _ddl_json
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _ddl_json  = ddl_json;
    
    _infoMessage("_demoblobs : ", _demoblobs);


    /** 
     * Maximal ratio (height/width) of thumbnail dimensions to optimize display.
     * @var {number} _max_ratio
     * @memberOf ipol.DrawBlobs~
     * @private
     * @defaults 0.5
     */
    var _max_ratio = 0.5; 
        
    //--------------------------------------------------------------------------
    /**
     * Pre-processes the demo information
     * @function _preprocessDemo
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _preprocessDemo = function() {
        _preprocessDemoOld();
        _preprocessDemoNew();
    }
    
    //--------------------------------------------------------------------------
    /**
     * Pre-processes the demo information, sets each blobset html_params
     * value containing the links of all the blob urls in the blobset
     * @function _preprocessDemoOld
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _preprocessDemoOld = function() {
        
        var blobs = _demoblobs.blobs;
        
        // preprocess HTML parameters string
        // for each blob set, in the form
        // html_params="url=XXXX&0:blob&1:blob&2:blob,blob etc ..."
        for(var i=0;i<blobs.length;i++)
        {
            var blobset = blobs[i];
            blobset[0].html_params = "url=" + _demoblobs.url + "&"
                // extract only contents of interest
            var blobset_contents = blobset.slice(1);
            blobset_contents.sort(function(a, b) {
                return (a.pos_in_set < b.pos_in_set ? -1 : (a.pos_in_set > b.pos_in_set ? 1 : 0));
            });
            var current_id = ""
            for (var idx = 0; idx < blobset_contents.length; idx++) {
                if (idx == 0) {
                    blobset[0].html_params += blobset_contents[idx].pos_in_set + ":";
                } else {
                    // if same id, separate by comma ...
                    if (blobset_contents[idx].pos_in_set == current_id) {
                        blobset[0].html_params += ",";
                    } else {
                        // else separate arguments
                        blobset[0].html_params += "&" + blobset_contents[idx].pos_in_set + ":";
                    }
                }
                current_id = blobset_contents[idx].pos_in_set;
                blobset[0].html_params += ipol.utils.blobhash_subdir(blobset_contents[idx].hash) + 
                    blobset_contents[idx].hash + blobset_contents[idx].extension;
            }
        }
        
    }
    
    //--------------------------------------------------------------------------
    /**
     * Pre-processes the demo information, sets each blobset form_params
     * value containing the links of all the blob urls in the blobset
     * @function _preprocessDemoNew
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _preprocessDemoNew = function() {
        
        var blobs = _demoblobs.blobs;
        
        // preprocess FormData blobset parameters as an object
        // for each blob set, in the form
        // form_params={url:XXXX,0:blob,1:blob,2:blob,blob etc ..."
        for(var i=0;i<blobs.length;i++)
        {
            var blobset = blobs[i];
            blobset[0].form_params = {};
            blobset[0].form_params["url"] = _demoblobs.url;
                // extract only contents of interest
            var blobset_contents = blobset.slice(1);
            blobset_contents.sort(function(a, b) {
                return (a.pos_in_set < b.pos_in_set ? 
                        -1 : 
                        (a.pos_in_set > b.pos_in_set ? 1 : 0));
            });
            for (var idx = 0; idx < blobset_contents.length; idx++) {
                var pos = blobset_contents[idx].pos_in_set;
                if (!blobset[0].form_params[pos]) {
                    blobset[0].form_params[pos]=[];
                }
                blobset[0].form_params[pos].push(
                    ipol.utils.blobhash_subdir(blobset_contents[idx].hash) +
                    blobset_contents[idx].hash + 
                    blobset_contents[idx].extension);
            }
            //_infoMessage("_preprocessDemo blobset ", i, 
            //             " form_params=",blobset[0].form_params);
        }
        
    }

    //--------------------------------------------------------------------------
    /**
     * Displays demo blobs and create events
     * @function _drawDemoBlobs
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _drawDemoBlobs = function() {
        _infoMessage("DrawDemoBlobs");
        $("#displayblobs").html(_createBlobSetDisplay());
        _demoBlobsEvents();
    }
    
    //--------------------------------------------------------------------------
    /**
     * Displays demo blobs and create events
     * @function _createBlobSetDisplay
     * @memberOf ipol.DrawBlobs~
     * @returns {string} the HTML code to display the blobsets
     * @private
     */
    var _createBlobSetDisplay = function()
    {
        var blobsets_html = "";
        
        var thumbnail_size   = $("#ThumbnailSize option:selected").text();
        var display_credits  = $("#ShowCreditsCheckbox").is(':checked');
        var display_titles   = $("#ShowTitlesCheckbox").is(':checked');
        
        _infoMessage("ThumbailSize is  ",$("#ThumbnailSize option:selected").text());
        
        // loop over blobsets
        for(var i=0;i<_demoblobs.blobs.length;i++)
        {
            var blobset = _demoblobs.blobs[i];
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
                var show_blob = true;
                var show_ellipsis = false;
                // if many blobs (>4) show only first and last ...
                if ((blobset[0].size>4)) {
                    show_blob = (idx===1)||(idx===blobset[0].size);
                    show_ellipsis = (idx===2);
                }
                
                if (!show_blob) {
                    if (show_ellipsis) {
                        blobset_html += "<td style='margin:0px;padding:0px;'> &hellip; </td>";
                    }
                    continue;
                }
                
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
                             +  '   src="'+_demoblobs.url_thumb+'/'
                             +  ipol.utils.blobhash_subdir(blobset[idx].hash)
                             + 'thumbnail_'+blobset[idx].hash+blobset[idx].extension+'" '
                             +  '   alt='   +blobset[idx].title
                             +  '   title="'+blobset[idx].title
                             +      ' (credits: '+blobset[idx].credit
                             +      ', tags:'+blobset[idx].tag
                             +      ', '+idx+'/'+blobset[0].size+' )" >&nbsp;' 
                             +  "</div> "
                             +  "</td>";
            } // end for idx
            blobset_html += "</tr>";
            if (display_titles||display_credits) {
                blobset_html += '<tr  style="background-color:#EEEEEE;">';
                blobset_html += '<th colspan="'+blobset[0].size+'" ';
                blobset_html +=   'style="max-width:'+(blobset[0].size*thumbnail_size)+'px;font-weight:normal;text-overflow:ellipsis;" >';
                //          We could use the blob name but in general each image has the same title
                //             which is a better name <span>{{blob_set[0].set_name}}</span>
                if (display_titles) {
                    if (blobset[0].set_name!="") {
                        blobset_html += '<font size="-1">'+blobset[0].set_name+'</font>';
                    } else {
                        blobset_html += '<font size="-1">'+blobset[1].title+'</font>';
                    }
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
    /**
     * Create demo blobs events
     * @function _demoBlobsEvents
     * @memberOf ipol.DrawBlobs~
     * @private
     */
    var _demoBlobsEvents = function() {
        
        var blobs = _demoblobs.blobs;
        
        // compute the total number of images to load
        // to adapt the height once all images are loaded
        var images_to_process = 0;
        for(var i=0;i<blobs.length;i++) {
            images_to_process += _demoblobs.blobs[i][0].size;
        }
        _infoMessage("images_to_process =", images_to_process);
        
        for(var i=0;i<blobs.length;i++) {
            // set click events on blobsets
            $("#blobset_"+i).click( {blobset_id: i}, function(event) {
                // empty results
                $("#ResultsDisplay").empty();
                $("#ResultsDisplay").removeData();
                // create an instance of DrawInputs
                var di = new ipol.DrawInputs(_ddl_json);
                di.setBlobSet(_demoblobs.blobs[event.data.blobset_id]);
                di.setInputOrigin("blobset");
                di.createHTML();
                di.loadDataFromBlobSet();
                // prepare to run the demo
                var run = new ipol.RunDemo(ddl_json,
                                           di.getInputOrigin(),
                                           di.getCropInfo(), 
                                           di.getBlobSet(),
                                           di.getDrawMask(),
                                           di.getDrawLines()
                                          );
                run.setRunEvent();
            }
            );
            // Set hover event on blobset
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
            // load thumbnails for this blobset
            var blobset = _demoblobs.blobs[i];
            _max_ratio = 0.5; 
            var processed_images = 0;
            for(var idx=1;idx<blobset[0].size+1;idx++)
            {
                // check if thumbnail load works, if not, hide the corresponding
                // image
                var tester=new Image();
                tester.src= _demoblobs.url_thumb+'/'+
                            ipol.utils.blobhash_subdir(blobset[idx].hash)+
                            'thumbnail_'+blobset[idx].hash+blobset[idx].extension;
                tester.onload = function() {
                    _max_ratio = Math.min(Math.max(_max_ratio,this.height/this.width),1);
                    processed_images++;
                    if (processed_images==images_to_process) {
                        _infoMessage("processed_images=",processed_images," / ",images_to_process);
                        _infoMessage("setting ratio to ",_max_ratio, " for blob ", i);
                        var thumbnail_size   = $("#ThumbnailSize option:selected").text();
                        var new_height = thumbnail_size*_max_ratio;
                        $(".select_input").css({'height'      :new_height+'px',               
                                                'line-height' :new_height+'px'});
                    }
                }; 
                tester.onerror = function(i,idx) { return function() {
                    console.info("tester.onerror blobset:",i," blob index:",idx);
                    $("#blob_"+i+"_"+idx).hide();
                    _infoMessage("failed to load blob image ",i," index ",idx);
                    processed_images++;
                    if (processed_images==images_to_process) {
                        _infoMessage("setting ratio to ",_max_ratio, " for blob ", i);
                        var thumbnail_size   = $("#ThumbnailSize option:selected").text();
                        var new_height = thumbnail_size*_max_ratio;
                        $(".select_input").css({'height'      :new_height+'px',               
                                                'line-height' :new_height+'px'});
                    }
                }; }(i,idx);
            } 
        }
    }

    //--------------------------------------------------------------------------
    // PUBLIC METHODS
    //--------------------------------------------------------------------------
    
    //--------------------------------------------------------------------------
    /**
     * Appends blobs to the demo blobs
     * @function appendBlobs
     * @memberOf ipol.DrawBlobs~
     * @param {object} db result from asking blob template 
     * @public
     */
    this.appendBlobs = function(db) {
        _infoMessage("appendBlobs ", _demoblobs, " -- ", db);
        _demoblobs.blobs = _demoblobs.blobs.concat(db.blobs);
        _this.updateDemoBlobs();
    }

    
    //--------------------------------------------------------------------------
    /**
     * Displays demo blobs
     * @function updateDemoBlobs
     * @memberOf ipol.DrawBlobs~
     * @public
     */
    this.updateDemoBlobs = function() {

        _infoMessage("demoblobs.blobs.length=",_demoblobs.blobs.length);
        
        var str = JSON.stringify(_demoblobs, undefined, 4);
//         $("#tabs-blobs pre").html(ipol.utils.syntaxHighlight(str));

        _preprocessDemo();
        _drawDemoBlobs();
        
        $("#ThumbnailSize")      .unbind().change( function() { 
            _infoMessage("ThumbnailSize changed");
            _drawDemoBlobs(); 
        });
        $("#ShowCreditsCheckbox").unbind().change( function() { 
            _infoMessage("ShowCreditsCheckbox changed");
            _drawDemoBlobs(); 
        });
        $("#ShowTitlesCheckbox") .unbind().change( function() { 
            _infoMessage("ShowTitlesCheckbox changed");
            _drawDemoBlobs(); 
        });
    }
        
    
};

//------------------------------------------------------------------------------
// STATIC METHODS
//------------------------------------------------------------------------------

//------------------------------------------------------------------------------
/**
 * function called when receiving the list of demo blobs for user selection
 * @param ddl_json {object} demo description object DDL
 * @returns {callback} returns the function that deals with the returned blobs
 * @function staticOnDemoBlobs
 * @memberOf ipol.DrawBlobs
 * @static
 */
ipol.DrawBlobs.staticOnDemoBlobs = function(ddl_json) {
    return function (demoblobs) {
        
//        console.info("*** OnDemoBlobs ", "demoblobs=",demoblobs);
//         console.info("ddl_json=",ddl_json);
        
        if (demoblobs.status=="KO") {
            $("#displayblobs").html("Failed to read demo blobs");
            // empty results
            $("#ResultsDisplay").empty();
            $("#ResultsDisplay").removeData();
            return;
        }
        
        var bc = new ipol.DrawBlobs(demoblobs, ddl_json);
        
        // Check for template
        if (demoblobs.use_template.hasOwnProperty('name')) {
            // get template blobs
            var template_name = demoblobs.use_template.name;
            console.info("*** getting template")
            ipol.utils.ModuleService(
                "blobs",
                "get_blobs_from_template_ws",
                "template="+template_name,
                function(db){bc.appendBlobs(db)}
            );
        } else {
            bc.updateDemoBlobs();
        }
        
    }
}
