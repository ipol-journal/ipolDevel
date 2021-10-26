"use strict"

let demo_id = getParameterFromURL('id');
// global, the requested page, null if undefined
let page = +getParameterFromURL('page');
if (page == null) page = -1;
let ddl;
/**
 * document.onload, global populate page
 */
$(document).ready(function() {
  $("#header").load("header.html");
  $("#footer").load("footer.html");

  // Read DDL and populate page
  fetchDDLInfo();
  fetchArchiveInfo();
});

async function fetchDDLInfo() {
  try {
    const demoinfoResponse = await fetch("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id + "&sections=archive,general");
    const data = await demoinfoResponse.json();
    if (data.status != "OK") returnToDemoList("Wrong demo id: " + demo_id);

    ddl = data.last_demodescription.ddl;
    $("#pageTitle").html(ddl.general.demo_title);
    $("#citation-link").attr('href', ddl.general.xlink_article);
    $("#articleTab").attr('href', ddl.general.xlink_article);
    $("#demoTab")[0].href = 'demo.html?id=' + demo_id;
  } catch {
    returnToDemoList("Failed to obtain the ddl: " + demo_id);
  }
}

async function fetchArchiveInfo() {
  try {
    const archiveResponse = await fetch('/api/archive/get_page?page=' + page + '&demo_id=' + demo_id);
    const archiveData = await archiveResponse.json();
    // default page should be last one
    if (page < 0) page = archiveData.meta.number_of_pages;
    $('header > p').before(`<h3>${archiveData.meta.number_of_experiments} public experiments since ${archiveData.meta.first_date_of_an_experiment.substr(0, 10)}</h3>`);
    let html = paging(archiveData.meta);
    for (const experiment in archiveData.experiments) {
      html += record(archiveData.experiments[experiment]);
    }
    html += paging(archiveData.meta);
    $("#results").append(html);
  } catch (e) {
    console.log(e);
    returnToDemoList("Failed to obtain the experiment page " + page + " for the demo " + demo_id);
  }
}

function returnToDemoList(errorMsg) {
  alert(errorMsg);
  window.location = '/demo';
}

/**
 * Page slider
 */
function paging(data) {
  if (data.number_of_pages <= 1) return "";
  if (page < 1 || page > data.number_of_pages) page = data.number_of_pages;
  const firstPageLink = page - 5;
  const lastPageLink = page + 5;
  let firstPageShown = (firstPageLink < 1) ? 1 : firstPageLink;
  let lastPageShown = (lastPageLink > data.number_of_pages) ? data.number_of_pages : lastPageLink;

  let html = '';
  html += '<nav class="paging">';
  if (page != 1) html += `<a href="?id=${demo_id}&page=1">First</a>`;
  if (page != 1) html += `<a href="?id=${demo_id}&page=${page - 1}">Previous</a>`;
  
  for (let i = firstPageShown; i <= lastPageShown; i++) {
    if (i == page) html += `<a href="?id=${demo_id}&page=${i}" class="active-page">${i}</a>`;
    else html += `<a href="?id=${demo_id}&page=${i}">${i}</a>`;
  }

  if (page != data.number_of_pages) html += `<a href="?id=${demo_id}&page=${(page + 1)}">Next</a>`;
  if (page != data.number_of_pages) html += `<a href="?id=${demo_id}&page=${(data.number_of_pages)}">Last</a>`;
  
  html += `<form class="paging">`;
  html += `<p>Go to page:</p>`;
  html += `<input type="number" name="page" placeholder="(1 ... ${data.number_of_pages})" min="1" max="${data.number_of_pages}">`;
  html += `<input type="hidden" name="id" value="${demo_id}">`;
  html += `<input type="submit" value="Go"></form>`;
  html += '</nav>';
  return html;
}

/**
 * Display a record, an experiment with meta and images
 */
function record(data) {
  let html = '<hr class="separator"/>';
  html += '<div class="record">';
  html += '<header>';
  html += `<div class="legend" id=${data.id}><p>Experiment <strong id="experiment-id">#${data.id}</strong>.</p><p>${data.date} UTC</p>`;

  var runtime = +data.parameters['run time'];
  if (runtime) html += '<p>(done in '+runtime.toFixed(3)+' s)</p>';
  
  html += '</div>';
  html += '</header>';

  if (data.parameters) {
    var pars = "";
    for (var paramName in data.parameters) {
      if (paramName == 'run time') continue;
      pars += '<tr>';
      pars += '<th>' + paramName + '</th>'
      pars += '<td>' + data.parameters[paramName] + '</td>'
      pars += '</tr>';
    }
    if (pars) {
      html += '<div class="parameters-container">';
      html += '<div class="parameters">';
      html += '<table class="pars">';
      html += '<caption>Parameters</caption>';
      html += pars;
      html += '</table>';
      html += '</div>'; // parameters
      html += '</div>'; // parameters-container
    }
  }

  html += '<div class="images-container">';
  var files_count = data.files.length;
  for (var i = 0; i < files_count; i++) {
    let isHiddenFile = ddl.archive.hidden_files ? Object.values(ddl.archive.hidden_files).includes(data.files[i].name) : false;
    if (!data.files[i].url_thumb || isHiddenFile) continue;
    html += `<a href="${data.files[i].url}"><img src="${data.files[i].url_thumb}" class="thumbnail">`;
    html += `<p class="image-name">${data.files[i].name}</p></a>`;
  }
  html += '</div>'; // images

  // files
  let files = "";
  for (let i = 0; i < files_count; i++) {
    let isHiddenFile = ddl.archive.hidden_files ? Object.values(ddl.archive.hidden_files).includes(data.files[i].name) : false;
    if (data.files[i].url_thumb || isHiddenFile) continue;
    let url = data.files[i].url;
    let ext = url.substr(url.lastIndexOf('.')+1);
    let downloadName = data.files[i].name + '.' + ext;
    files += '<a class="file ' + ext + '" target="_blank" href="' + url + '" download="' + downloadName + '">' + data.files[i].name + '</a>';
  }

  if (files) { 
    html += "<div class=files ><p id=files-text>Files</p>: "; 
    html += files; 
    html += '</div>';
  }

  if (ddl.archive.enable_reconstruct && data.execution) {
    let link = `/demo/clientApp/demo.html?id=${demo_id}&archive=${data.id}`
    html += `<button class="reconstruct-btn btn" onclick="window.location.href ='${link}'">Reconstruct</button>`;
  }

  html += '</div>';
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
