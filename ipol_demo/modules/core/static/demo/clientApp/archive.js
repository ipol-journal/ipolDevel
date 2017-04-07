/**
 * @file this file contains the documentReady() function,
  and deals with the initial interactions of the main page: enable page tabulations,
  set events for several buttons, set events for input description and parameters
  description modal windows, for upload modal window, set event for browser history,
  list available demos and create the demo selection. It deals with
  the demo selection in the function 'Input-Controller'. It calls methods or classes
  from other files to display the demo page: input blobs, descriptions, parameters,
  archive information. 
  The demo can be selected
  from three different inputs (demo_origin enumeration): user widget selection,
  url or browser history. The function 'Set-Archive-Experiment' sets the demo
  page information based on an archive experiment, it is called if the url parameters
  contain an experiment id together with the demo id.
 * @version 0.1
 */

// using strict mode: better compatibility
"use strict";

/**
 * Image Processing OnLine (IPOL) journal demo system namespace
 * @namespace
 */
var ipol = ipol || {};

//------------------------------------------------------------------------------
/**
 * Get the url parameters
 * @returns {object} containing the name and values of the parameters
 */
ipol.getUrlParameters = function() {

    var url_params = {};
    location.search.substr(1).split("&").forEach(function(item) {
        var s = item.split("="),
            k = s[0],
            v = s[1] && decodeURIComponent(s[1]);
        (k in url_params) ? url_params[k].push(v) : url_params[k] = [v]
    });
    return url_params;
}

//------------------------------------------------------------------------------
/**
 * Function called when the demo list is received
 * @param {object} demolist returned by the demoinfo module
 */
ipol.onDemoInfoDemoList = function(demolist)
{
    //--------------------------------------------------------------------------
    this.InfoMessage = function( ) {
        if (this.verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- onDemoInfoDemoList ----");
            console.info.apply(console,args);
        }
    }
    this.verbose=false;

    var dl = demolist;
    if (dl.status == "OK") {
        this.InfoMessage("demo list is ",dl);
    }

    // Get the URL parameters
    var url_params = ipol.getUrlParameters();
    this.InfoMessage("url parameters = ",url_params);
    // Check for 'id' parameter
    if (url_params["id"]!=undefined) {
        var demo_id = url_params["id"][0];
        this.InfoMessage("demo_id = ", demo_id);
    }

    // create a demo selection
    var html_selection = "<select id='demo_selection'>";
    var demo_pos = -1;
    for (var i=0; i<dl.demo_list.length; i++) {
        if (dl.demo_list[i].editorsdemoid==demo_id) {
            this.InfoMessage("found demo id at position ", i);
            demo_pos=i;
        }
        html_selection += '<option value = "'+i+'">'
        html_selection += dl.demo_list[i].editorsdemoid +
                            '  '+ dl.demo_list[i].title
        html_selection += '</option>'
    }
    html_selection += "</select>";

    $("#demo-select").html(html_selection);

    if (demo_pos!=-1) {
        $("#demo_selection").val(demo_pos);
        ipol.setDemoPage(dl.demo_list[demo_pos].editorsdemoid,
                        ipol.demo_origin.url
                    );
    }

    $("#demo-select").data("demo_list",dl.demo_list);
    $("#demo-select").change(
        function() {
            var pos =$( "#demo-select option:selected" ).val();
            ipol.setDemoPage(dl.demo_list[pos].editorsdemoid,
                        ipol.demo_origin.select_widget
                        );
        });

    if (servers.in_production) {
        $("#demo-select").hide();
    }
};

//------------------------------------------------------------------------------
/**
 * List all demos and select one
 */
ipol.listDemos = function (){
//     console.info("get demo list from server");
    ipol.utils.ModuleService(
        'demoinfo',
        'demo_list',
        '',
        ipol.onDemoInfoDemoList
    );
};

/**
 * Enum for demo origin
 * @readonly
 * @enum {number}
 */
ipol.demo_origin =  {
    /** demo selected from the webpage selector */
    select_widget:0,
    /** demo specified in the url parameters */
    url:1,
    /** demo obtained from using the browser history features */
    browser_history:2
};

//-----------------------------------------------------------------------
/**
 * Starts everything needed for demo input tab.
 * @param {number} demo_id the demo id
 * @param {ipol.demo_origin} origin of enum type demo_origin
 * @param {callback} func
 * @fires demoinfo:get_ddl
 * @fires blobs:get_blobs_of_demo_by_name_ws
 * @fires archive:get_experiment
 */
ipol.setDemoPage = function (demo_id,origin,func) {

    $('#tabs-nohdr').tabs('option', 'active', 2);

    if (origin===undefined) {
        origin=ipol.demo_origin.select_widget;
    }

    if (demo_id > 0) {
        ipol.utils.ModuleService(
            'demoinfo',
            'get_ddl',
            'demo_id=' + demo_id,
            function(demo_ddl) {

                if (demo_ddl.status == "OK") {
                    var ddl_json = ipol.utils.DeserializeJSON(demo_ddl.last_demodescription.json);
                } else {
                    console.error(" --- failed to read DDL");
                }

                // update document title
                $('title').html("IPOL Journal &middot; "+ddl_json.general.demo_title);
                // set title on top of the page
                $("#pagetitle").html(ddl_json.general.demo_title);
                // article link
                $("#tabs-nohdr .algo").html("<a style='display:block' "+
                                            "  href='"+ddl_json.general.xlink_article+"'>article</a>");
                //The href in the tabs are rewritten to get access to archive.html or demo.html
                $("#tabs-nohdr .tabs_archive").html("<a style='display:block' "+
                                            "  href='archive.html?id="+demo_id+"'>archive</a>");
                $("#tabs-nohdr .tabs_run").html("<a style='display:block' "+
                                            "  href='demo.html?id="+demo_id+"'>demo</a>");
                // update article link
                $("#citation a").attr("href", ddl_json.general.xlink_article);

                // Display archive information
                var ar = new ipol.ArchiveDisplay();
                // get and display the last archive page
                ar.getArchive(demo_id,-1);

            });
    }

}

//------------------------------------------------------------------------------
/**
 * Starts processing when document is ready
 */
ipol.documentReady = function () {

    $("#tabs-nohdr").tabs();

    if (servers.in_production) {
        $("#tabs_ddl").hide();
    }

    ipol.listDemos();

}
$(document).ready(ipol.documentReady);