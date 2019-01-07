"use strict"

var demo_id = getParameterFromURL('id');
// global, the requested page, null if undefined
var page = +getParameterFromURL('page');
var ddl;
/**
 * document.onload, global populate page
 */
$(document).ready(function() {
  $("#header").load("header.html");
  $("#footer").load("footer.html");

  // Read DDL and populate page
  var url = "/api/demoinfo/get_interface_ddl?demo_id=" + demo_id + "&sections=archive,general";
  $.getJSON(url, function(data) {
    if (data.status != "OK") returnToDemoList("Wrong demo id: " + demo_id);

    ddl = JSON.parse(data.last_demodescription.ddl);
    $("#pageTitle").html(ddl.general.demo_title);

    $(".citation").html('<span>Please cite <a id="citation-link">the reference article</a> if you publish results obtained with this online demo.</span>');
    $("#citation-link").attr('href', ddl.general.xlink_article);
    $("#articleTab").attr('href', ddl.general.xlink_article);
    $("#demoTab")[0].href = 'demo.html?id=' + demo_id;

    if ( page == null ) page = -1;
    var url = '/api/archive/get_page?page=' + page + '&demo_id=' + demo_id;
    $.getJSON(url, function(data) {
      // default page should be last one
      if (page < 0) page = data.meta.number_of_pages;
      var html = '';
      html += '\n<header>';
      html += '\n<h3>' + data.meta.number_of_experiments + ' public experiments since ' + data.meta.first_date_of_an_experiment.substr(0, 10) + '</h3>';
      html += '\n<p class="p">This archive is not moderated. In case you uploaded images that you don’t want that appear in the archive, please contact the editor in charge. In case of copyright infringement or similar problems, please <a href="https://tools.ipol.im/wiki/ref/demo_input/#archive-cleanup">contact us</a> to request the removal of some images. Some archived content may be deleted by the editorial board for size matters, inadequate content, user requests, or other reasons.</p>';
      html += '\n</header>';
      html += paging(data.meta);
      var max = data.experiments.length;
      for (var i=0; i < max; i++) 
        html += record(data.experiments[i]);

      html += paging(data.meta);
      $("#results").html(html);

      var reconstruct_buttons = $('.reconstruct-btn');
      for (let i = 0; i < reconstruct_buttons.length; i++) 
        $(reconstruct_buttons[i]).addClickEvent();

    })
    .fail(function() {
      returnToDemoList("Failed to obtain the experiment page " + page + " for the demo " + demo_id);
    });
  })
  .fail(function() {
    returnToDemoList("Failed to obtain the ddl: " + demo_id);
  });
});

$.fn.addClickEvent = function() {
  $(this).click(function(){
      window.location = "/demo/clientApp/demo.html?id=" + demo_id + "&archive=" + $(this)[0].getAttribute('data-experiment-id');
  });
}

function returnToDemoList(errorMsg) {
  alert(errorMsg);
  window.location = '/demo';
}

/**
 * Page slider
 */
function paging(data) {
  if (page < 1 || page > data.number_of_pages) page = data.number_of_pages;
  var diff = 5;
  var from = page - diff; 
  from = (from < 1) ? 1 : from;
  var to = page + diff; 
  to = (to > data.number_of_pages) ? data.number_of_pages : to;

  var html = '';
  html += '\n<nav class="paging">';
  if (from > 1) 
    html += '\n<a href="?id=' + demo_id + '&page=' + (from-1) + '">◀◀</a>';
  
  for (var i=from; i<=to; i++) {
    if (i == page) {
      html += '\n<form class="page">';
      html += '\n  <input name="id" type="hidden" value="' + demo_id + '"/>';
      html += '\n  <select name="page" onchange="this.form.submit()">';
      for (var j=1; j <= data.number_of_pages; j++) {
        html += '\n    <option';
        if (j == page) html += ' selected="selected"';
        html += '>' + j + '</option>';
      }
      html += '\n  </select>';
      html += '\n</form>';
    }
    else 
      html += '\n<a href="?id=' + demo_id + '&page=' + i + '">'+i+'</a>';
  }

  if (to < data.number_of_pages) 
    html += '\n<a href="?id=' + demo_id + '&page=' + (to+1) + '">▶▶</a>';
  
  html += '\n</nav>';
  return html;
}

/**
 * Display a record, an experiment with meta and images
 */
function record(data) {
  var html = '';
  html += '\n<hr class="separator"/>';
  html += '\n<div class="record">';
  html += '\n<header>';
  html += '\n<div class="legend" id=' + data.id + '>Experiment <b class="id">#'+data.id+'</b>.<br/>'+data.date;

  var runtime = +data.parameters['run time'];
  if (runtime) html += ' (done in '+runtime.toFixed(3)+' s)';
  
  html += '.</div>';
  html += '\n</header>';
  html += '\n<div class="middle">';

  if (data.parameters) {
    var pars = "";
    for (var key in data.parameters) {
      if (key == 'run time') continue;
      pars += '\n<tr>';
      pars += '<th>' + key + '</th>'
      pars += '<td>' + data.parameters[key] + '</td>'
      pars += '</tr>';
    }
    if (pars) { // maybe no parameters
      html += '\n<div>'; // the flex container
      html += '\n<div class="pars">';
      html += '\n<table class="pars">';
      html += '\n<caption>Parameters</caption>';
      html += pars;
      html += '\n</table>';
      html += '\n</div>';
      html += '\n</div>';
    }
  }

  html += '\n<div class="thumbs">';
  var files_count = data.files.length;
  for (var i = 0; i < files_count; i++) {
    let isHiddenFile = ddl.archive.hidden_files ? Object.values(ddl.archive.hidden_files).includes(data.files[i].name) : false;
    if (!data.files[i].url_thumb || isHiddenFile) continue;
    html += '\n<a href="' + data.files[i].url + '" target="_blank" class="thumb">';
    html += '\n<img class="thumb" src="' + data.files[i].url_thumb + '"/>';
    html += '\n' + data.files[i].name;
    html += '\n</a>';
  }
  html += '\n</div>'; // thumbs
  html += '\n</div>'; // middle

  // other files, below thumbnails
  var files = "";
  for (var i = 0; i < files_count; i++) {
    let isHiddenFile = ddl.archive.hidden_files ? Object.values(ddl.archive.hidden_files).includes(data.files[i].name) : false;
    if (data.files[i].url_thumb || isHiddenFile) continue;
    var url = data.files[i].url;
    var ext = url.substr(url.lastIndexOf('.')+1);
    // not empty string, add comma.
    if (files) files += ", ";
    files += '<a class="file ' + ext + '" target="_blank" href="' + url + '">' + data.files[i].name + '</a>';
  }

  if (files) { 
    html += "\n<div class=files-footer ><b>Files</b>: "; 
    html += files; 
    html += '.</div>';
  }

  if (ddl.archive.enable_reconstruct && data.execution)
    html += '\n<button class="reconstruct-btn btn" data-experiment-id=' + data.id + '>Reconstruct</button>';

  html += '\n</div>\n';
  return html;
}

function getParameterFromURL(name) {
  var url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
  results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}
