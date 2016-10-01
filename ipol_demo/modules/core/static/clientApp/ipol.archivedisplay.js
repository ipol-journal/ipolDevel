/**
 * @file 
 * this file contains the code that renders and deals with the demo archives
 * associated with ipol_demo.html and ipol_demo.js
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

// ipol application namespace
var ipol = ipol || {};


//------------------------------------------------------------------------------
/**
 * Display demo archives
 * @constructor
 */
ipol.ArchiveDisplay = function()
{
    
    /** 
     * By convention, we create a private variable '_this' to
     * make the object available to the private methods.
     * @var {object} _this
     * @memberOf ipol.ArchiveDisplay~
     * @private
     */
    var _this = this;

    /** 
     * Enable/Disable display of (tracing/debugging) 
     * information in browser console.
     * @var {boolean} _verbose
     * @memberOf ipol.ArchiveDisplay~
     * @private
     */
    var _verbose=false;
    

    /** 
     * number of current displayed page
     * @var {number} _current_page
     * @memberOf ipol.ArchiveDisplay~
     * @private
     */
    var _current_page=0;
        
    //--------------------------------------------------------------------------
    /**
     * Displays message in console if verbose is true
     * @function _infoMessage
     * @memberOf ipol.ArchiveDisplay~
     * @private
     */
    var _infoMessage = function( ) {
        if (_verbose) {
            var args = [].slice.call( arguments ); //Convert to array
            args.unshift("---- ArchiveDisplay ----");
            console.info.apply(console,args);
        }
    }

    //--------------------------------------------------------------------------
    /**
     * Adds the links to the different archive pages
     * @function _archivePages
     * @memberOf ipol.ArchiveDisplay~
     * @param   {object} res
     * @returns {string} HTML code to display the page links
     * @private
     */
    var _archivePages = function(res) {
        var html = "pages ";
        for(var p=1;p<=res.meta.number_of_pages;p++)
        {
            html += "<span class=set_page_"+p+">"+p+"</span>&nbsp;";
        }
        return html;
    }

    //--------------------------------------------------------------------------
    /**
     * Displays the contents of one experiment
     * @function _oneArchive
     * @memberOf ipol.ArchiveDisplay~
     * @param   {number} demo_id    demo id
     * @param   {object} exp        experiment information
     * @returns {string} HTML code to display one archive experiment
     * @private
     */
    var _oneArchive = function(demo_id,exp) {
        var html = "";
        html += '<div class="bucket" >';
        //style="display:inline-block;vertical-align: top;">';
        
        // html code for files without visual representation (VR)
        var html_files  = '';
        // html code for files with visual representation
        var html_images = '';
        
        var HasVisualRepresentation = function(file) {
            // for the moment, just check if the file ends with png
            // later use url_thumb property to decide
            _infoMessage("file.url = ", file.url, " png?",file.url.endsWith('.png'));
            return file.url.endsWith('.png');
        }.bind(this);
        
        $.each(exp.files,
            function(index,file) {
                if (HasVisualRepresentation(file)) {
                // if VR
                    html_images += '<a href="'+file.url+'">';
                    html_images += '<img class="thumbnail" src="'+
                                    file.url_thumb+'" title="'+
                                    file.name+'" alt="'+file.name+'"/></a>';
                } else {
                // if no VR
                    html_files += '<a href="'+file.url+'" title="' + 
                                    file.name+'">' + file.name+'</a> &nbsp;';
                    if (file.name=="results from experiment") {
                        $.getJSON(file.url,
                            function(data){
                                console.info("got results :", data);
                            }
                        );
                    }
                }
            }
        );
        
        _infoMessage("exp=",exp);
        
        // info table
        html += '<table class="info">';
            html += '<tr>';
            html += '<th style="text-align:center;vertical-align:middle;">Experiment</th>';
            // todo link to experiment details ...
            //html += '<td><a href="ipol_demo.html?id='+demo_id+'&exp='+exp.id+
            //        '"  target="_blank">Experiment '+exp.id+'</a>';
            
            html += '<td>Experiment '+exp.id+'</a>';
            html += '</td>';
            html += '</tr>';
            html += '<tr>';
            html += '<th style="text-align:center;vertical-align:middle;">date </th>';
            html += '<td> '+exp.date+'</td>';
            html += '</tr>';
            $.each(exp.parameters,
                function(param,value) {
                    html += '    <tr>';
                    html += '      <th style="text-align:center;vertical-align:middle;">'+
                            param+'</th>';
                    html += '      <td>'+value+'</td>';
                    html += '    </tr>';
                }
            );
            
            html += '<tr>';
            html += '  <th style="text-align:center;vertical-align:middle;">files</th>';
            html += '  <td>';
            html += html_files;
            html += '  </td>';
            html += '</tr>';
        html += '  </table>';
        // thumbnails table
        html += '<table class="thumbnails">';
            html += '<tr>';
            html += '  <th style="text-align:center;vertical-align:middle;">Images</th>';
            html += '</tr>';
            html += '<tr>';
            html += '  <td>';
            html += html_images;
            html += '  </td>';
            html += '</tr>';
        html += '  </table>';
        html += '</div>';
        html += '<br/>';
        html += '<hr class="clear">';
        
        return html;
    }

    //--------------------------------------------------------------------------
    /**
     * Create the HTML code for the current page
     * @function _createCurrentPage
     * @memberOf ipol.ArchiveDisplay~
     * @param   {object} res          result object obtained from archive module
     * @param   {number} demo_id      demo id
     * @param   {number} page_number  page number to display
     * @returns {string} HTML code to display the current archive page
     * @private
     */
    var _createCurrentPage = function(res,demo_id,page_number) {
        
        var meta_info       = res["meta"];
        var nb_experiments  = meta_info["number_of_experiments"];
            
        //             if number_of_experiments == '0': 
        //                 #Empty list. No experiments in the archive
        //                 archive_experiments = []
        //                 return self.tmpl_out("archive_index.html", archive_list=archive_experiments, page=0, 
        //                                      number_of_experiments=0, nbpage=0,first_date='never')           
        /*            
                    else:*/
                
        var first_date              = meta_info["first_date_of_an_experiment"];
        var nb_pages                = meta_info["number_of_pages"];
        
        if (page_number===undefined) {
            page_number = nb_pages;
        }
        // the last page is displayed if the page_number is out of range
        if ((page_number<1)||(page_number>nb_pages))  { 
            page_number=nb_pages;
        }
        _current_page=page_number;
        
        var nb_experiments_per_page = meta_info["number_of_experiments_in_a_page"];

        var html = "";
        
        // need to have id=content for CSS compatibility ...
        html += '<div id="content">';
        html += '<div class="archive_index" >';
        html += '<p>';
        html += nb_experiments+' public experiments since '+first_date+'.<br />';
        html += 'This archive is not moderated.';
        html += 'In case you uploaded images that you don\'t want that appear in'+ 
                'the archive, you can remove them by clicking on the corresponding key '+
                'and then clicking over the "delete this entry" button. '+
                'This button appears only for the experiments performed by the user '+
                'during the last 24 hours.<br>';
        html += 'In case of copyright infringement or similar problem, please '+
                '<a href="https://tools.ipol.im/wiki/ref/demo_input/#archive-cleanup">'+
                'contact us</a> to request the removal of some images.'+
                'Some archived content may be deleted by the editorial board for size '+
                'matters, inadequate content, user requests, or other reasons.';
        html += '</p>';
//         html += '<button id="ReloadArchive">Reload</button> <br/>';

        var html_pages = _archivePages(res);
        html += html_pages;

        html += '<hr class="clear">';
        $.each(res.experiments, 
               function(index,exp) {
                    html += _oneArchive(demo_id,exp);
               }.bind(this));

        html += html_pages;
        html += '</div>';
        html += '</div>';
        return html;
    }


    //--------------------------------------------------------------------------
    /**
     * Create the page events
     * @function _createPageEvents
     * @memberOf ipol.ArchiveDisplay~
     * @param   {number} demo_id      demo id
     * @param   {object} res          result object obtained from archive module
     * @private
     */
    var _createPageEvents = function(demo_id,res) {
        var meta_info = res["meta"];
        var nb_pages  = meta_info["number_of_pages"];
        
        $(".set_page_"+_current_page).css("font-weight","bold");
        for(var i=1;i<=nb_pages;i++) {
            $(".set_page_"+i).unbind().click(
                function(demoid,page) { 
                    return function() 
                    { 
                        _this.getArchive(demoid,page);
                    }
                } (demo_id,i)
            );
            // underline on hover
            $(".set_page_"+i).hover(
                function(){ $(this).css("text-decoration", "underline"); },
                function(){ $(this).css("text-decoration", "none");    }
            );
        }
        
        // commented reload button
        // // $( "#ReloadArchive" ).unbind("click");
        // $("#ReloadArchive").button().on("click", 
        //             function(obj,demoid) { 
        //                 return function() 
        //                 { 
        //                     obj.getArchive(demoid,this.current_page);
        //                 }
        //             } (this,demo_id)
        // );
    }
        
    //--------------------------------------------------------------------------
    /**
     * Gets and displays archive contents for the given demo and page number 
     * if the page number is undefined or out of range, 
     * the last page is displayed.
     * @function getArchive
     * @memberOf ipol.ArchiveDisplay~
     * @param   {number} demo_id      demo id
     * @param   {number} page_number  page number
     * @public
     */
    this.getArchive = function(demo_id,page_number) {
        
        var url_params =    'demo_id='    + demo_id + '&page='+page_number;
        ipol.utils.ModuleService("archive","get_page",url_params,
            function(res) {
                _infoMessage("archive result : ",res);
                if (res['status']==='OK') {
                    var html = _createCurrentPage(res,demo_id,page_number);
                    $("#tabs-archive").html(html);
                    _createPageEvents(demo_id,res);
                }
            }.bind(this));
    }
}


//------------------------------------------------------------------------------
/**
 * search and returns the url in archive of a given result filename
 * if not found returns undefined
 * @function staticFindArchiveUrl
 * @memberOf ipol.ArchiveDisplay
 * @static
 * @param {string} filename        filename to seach for in archive experiment
 * @param {object} ddl_archive_files list of archive files and their descriptions
 * @param {object[]} experiment_files array containing the experiment files
 * @returns {string} url of the found file or undefined
 */
ipol.ArchiveDisplay.staticFindArchiveUrl = function(filename,ddl_archive_files,
                                                experiment_files) {
    var archive_input_description = ddl_archive_files[filename];
    if (archive_input_description) {
        // find file url in archive
        for(var i=0; i<experiment_files.length;i++) {
            if (experiment_files[i].name === archive_input_description) {
                return experiment_files[i].url;
            }
        }
    }
    return undefined;
}
