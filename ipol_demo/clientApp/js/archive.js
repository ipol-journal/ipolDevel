"use strict"

// global, the demo id
var demo_id = getParameterByName('id');
// global, the requested page, null if undefined
var page = getParameterByName('page');

/**
 * document.onload, global populate page
 */
$(document).ready(function() {
  $("#header").load("header.html");
  $("#footer").load("footer.html");
  // if storage was used, clear it ?
  // sessionStorage.clear();
  // populate page from infos about the demo
  var url = "/api/demoinfo/get_interface_ddl?demo_id=" + demo_id;
  $.getJSON(url, function(data) {
    // ddl is provided as a string (why ? isn't it correct json ?)
    var ddl = JSON.parse(data.last_demodescription.ddl);
    // console.log(ddl);
    $("#pageTitle").html(ddl.general.demo_title);
    // this message is shared with demo.js
    $(".citation").html('<span>Please cite <a id="citation-link">the reference article</a> if you publish results obtained with this online demo.</span>');
    $("#citation-link").attr('href', ddl.general.xlink_article);
    $("#articleTab").attr('href', ddl.general.xlink_article);
    $("#demoTab")[0].href = 'demo.html?id=' + demo_id;
  })
  .fail(function() {
    console.log("archive.js — ddl load fail "+url);
    // strange bug if ddl not found but archive found, maybe whe should return here
  });
  if ( page == null ) page = -1;
  var url = '/api/archive/get_page?page=' + page + '&demo_id=' + demo_id;
  $.getJSON(url, function(data) {
    // default page should be last one
    if (page < 0) page = data.meta.number_of_pages;
    var html = '';
    html += '\n<header>';
    html += '\n<h3>'+data.meta.number_of_experiments+' public experiments since '+data.meta.first_date_of_an_experiment.substr(0, 10)+'</h3>';
    html += '\n<p class="p">This archive is not moderated. In case you uploaded images that you don’t want that appear in the archive, please contact the editor in charge. In case of copyright infringement or similar problems, please <a href="https://tools.ipol.im/wiki/ref/demo_input/#archive-cleanup">contact us</a> to request the removal of some images. Some archived content may be deleted by the editorial board for size matters, inadequate content, user requests, or other reasons.</p>';
    html += '\n</header>';
    html += paging(data.meta);
    var max = data.experiments.length;
    for (var i=0; i < max; i++) {
      html += record(data.experiments[i]);
    }
    html += paging(data.meta);
    $("#results").html(html);

    var legends = $(".legend");
    for (let i = 0; i < legends.length; i++) {
      if (data.experiments[i].execution) $("#" + legends[i].id).addClickEvent();
    }

  })
  .fail(function() {
    console.log("archive.js — page not found "+url);
    // strange bug if ddl not found but archive found, maybe whe should return here
  });
});

$.fn.addClickEvent = function() {
  $(this).css({'cursor': 'pointer'});
  $(this).click(function(){
      window.location = "/demo/clientApp/demo.html?id=" + demo_id + "&archive=" + $(this)[0].id;
  });
}

/**
 * Page slider
 */
function paging(data) {
  var html = '';
  html += '\n<nav class="paging">';
  for (var i=1; i<=data.number_of_pages; i++) {
    html += '\n<a href="?id=' + demo_id + '&page=' + i + '"';
    if ( i == page ) html += ' class="this"';
    html += '>'+i+'</a>';
  }
  // 23
  // ◀
  // ▶
  // 1
  html += '\n</nav>';
  return html;
}

/**
 * Display a record, an experiment with metas and images
 */
function record(data) {
  var html = '';
  html += '\n<hr class="separator"/>';
  html += '\n<div class="record">';
  html += '\n<header>';
  html += '\n<div class="legend" id=' + data.id + '>Experiment <b class="id">#'+data.id+'</b>.<br/>'+data.date;
  // run time ? seconds ? important ?
  var runtime = data.parameters['run time']+0;
  if (runtime) {
    html += ' (done in '+runtime.toFixed(3)+' s)';
  }
  html += '.</div>';

  html += '\n</header>';

  // contain pars and thumbs
  html += '\n<div class="middle">';

  // loop on parameters
  if (data.parameters) {
    var pars = "";
    for (var key in data.parameters) {
      if (key == 'run time') continue;
      pars += '\n<tr>';
      pars += '<th>'+key+'</th>'
      pars += '<td>'+data.parameters[key]+'</td>'
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
  var max = data.files.length;
  for (var i = 0; i < max; i++) {
    if (!data.files[i].url_thumb) continue;
    html += '\n<a href="'+data.files[i].url+'" target="_blank" class="thumb">';
    html += '\n<img class="thumb" src="'+data.files[i].url_thumb+'"/>';
    html += '\n'+data.files[i].name;
    html += '\n</a>';
  }
  html += '\n</div>'; // thumbs

  html += '\n</div>'; // middle



  // other files, below thumbnails
  var files = "";
  var max = data.files.length;
  for (var i = 0; i < max; i++) {
    if (data.files[i].url_thumb) continue;
    var url = data.files[i].url;
    var ext = url.substr(url.lastIndexOf('.')+1);
    // not empty string, add comma.
    if (files) files += ", ";
    files += '<a class="file '+ext+'" target="_blank" href="'+url+'">'+data.files[i].name+'</a>';
  }
  if (files) {
    html += '\n<footer><b>Files</b>: ';
    html += files;
    html += '.</footer>';
  }
  html += '\n</div>\n';
  return html;
}

function getParameterByName(name) {
  var url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
     results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}
