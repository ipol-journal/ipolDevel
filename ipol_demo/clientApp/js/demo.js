"use strict"

var demo_id, ddl, experiment, work_url, files, mapInput = [];

$(document).ready(function() {
  demo_id = getParameterFromURL('id');

  var demo_id_is_number = (/^\d+$/.test(demo_id));
  if (demo_id_is_number) {
    $("#header").load("header.html");
    $("#inputEditorContainer").load("editor.html");
    $("#parameters").load("parameters.html");
    $("#footer").load("footer.html");
    sessionStorage.clear();
    
    fetchData();
    $("#demoTab")[0].href = 'demo.html?id=' + demo_id;
  } else
    showWrongDemoIdError();
})

window.onpopstate = function() {
  hideStatusContainer();
  $("#inputEditorContainer").empty();

  if (getParameterFromURL('key')) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getParameterFromURL('key'));
  else if (getParameterFromURL('archive')) loadExecution("/api/archive/experiment/" + getParameterFromURL('archive'));
  else {
    $('.results').addClass('di-none');
    $('.results-container').empty();
  }
} 

async function fetchData() {
  await getDDL();
  await getBlobSets();
  if (getParameterFromURL('key')) loadExecution(`/api/core/load_execution?demo_id=${demo_id}&key=${getParameterFromURL('key')}`);
  if (getParameterFromURL('archive')) loadExecution(`/api/archive/experiment/${getParameterFromURL('archive')}`);
}

function getBlobSets() {
  return fetch(`/api/blobs/demo_blobs/${demo_id}`)
    .then(handleErrors)
    .then(response => response.json())
    .then(blobs => {
      console.log('Blobs', blobs);
      helpers.addToStorage('blobs', blobs);
      input.printSets(blobs);
    })
    .catch(error => {
      alert(error, 'Network error. Cannot reach Blobs service.');
    });
}

function getDDL() {
  return fetch(`/api/demoinfo/get_interface_ddl?demo_id=${demo_id}`)
  .then(handleErrors)
  .then(response => response.json())
  .then(responseJSON => {
    ddl = responseJSON.last_demodescription.ddl;

    // Map
    let mapInputs = ddl.inputs?.filter(input => input.type == "map");
    if (mapInputs?.length > 0) {
      let center = mapInputs[0].center;
      if (!center) center = [2.294226116367639, 48.85813310909694]; // default location [lng, lat]
      printMapPanel(center);
      helpers.setOrigin('upload');
    }

    // Archive
    if (ddl.hasOwnProperty('archive')) {
      $('#archiveTab').attr('href', 'archive.html?id=' + demo_id);
    } else {
      $("#archiveTab").css({'display': 'none'});
    }
    loadDemoPage();
    if (ddl.general.custom_js) loadDemoExtrasJS();

  })
  .catch(error => {
    showWrongDemoIdError();
  });
}

function handleErrors(response) {
  if (!response.ok) throw Error(response.statusText);
  return response;
}

function loadDemoPage(){
  displayDemoHeader();
  parameters.printParameters();
  if (ddl.general.description) displayDemoDescription();
  if (ddl.inputs) displayInputHeaders();
}

function loadDemoExtrasJS() {
  var url = ddl.general.custom_js;
  $.getScript(url)
    .fail(function () { console.error("Could not load the script: " + url); })
}

function displayDemoDescription(){
  $(".citation").after('<div class="container description-container"></div>');
  $(".description-container").append('<h1 class="container-title m-y-5">Description</h1>')
                             .append('<p class=description > ' + ddl.general.description + '</p>');
}

function displayInputHeaders() {
  $(".inputContainer, #inputEditorContainer").removeClass('di-none');
  input.displayInputInformationIcon();
  upload.printUploads();
}

function displayDemoHeader() {
  $("#pageTitle").html(ddl.general.demo_title);
  $("#articleTab, #citation-link").attr('href', ddl.general.xlink_article);
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

/* 
This implements the mechanism that allows to reconstruct an experiment from the temporal folder or archive, depending on the url.
*/
async function loadExecution(url){
  if (ddl == null && helpers.getFromStorage("blobs") == null) return;
  const response = await fetch(url);
  const data = await response.json();
  if (response.status === 201 || response.status === 200) {
    if(getParameterFromURL("archive")){ //Archive reconstruction
      experiment = data;
      var execution = JSON.parse(experiment.execution);
    }else{ //KEY reconstruction
      experiment = JSON.parse(data.experiment);
      var execution = experiment;
    }

    renderExperiment(execution.request, execution.response);
  } else {
    alert(data.error);
    window.location.href = "demo.html?id=" + demo_id;
  }
}

function renderExperiment(run_request, execution_response){
  work_url = execution_response.work_url;

  if (!$.isEmptyObject(run_request.params)) parameters.setParametersValues(run_request.params);
  if (run_request.origin == "blobSet") setEditor(run_request.setId, run_request.crop_info);
  if (run_request.origin == "upload") setFiles(run_request);
  if (run_request.private_mode) $('#privateSwitch').prop('checked', true);
  results.draw(execution_response);
}

function showWrongDemoIdError(){
  alert("Wrong demo id: " + demo_id);
  window.location = '/demo';
}

async function setFiles(request){
  files = Array(ddl.inputs.length);
  var blobs = [];
  var fetched_files = [];
  var isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  var isMSEdge = window.navigator.userAgent.indexOf('Edge') > -1;
  
  for (let [i, input] of ddl.inputs.entries())
    fetched_files[i] = new Promise((resolve) => {
      let file_url = getFileURL('input_' + i + input.ext);
      resolve(fetch(file_url));
    })
    
  fetched_files = await Promise.all(fetched_files)
  for (let [i, file] of fetched_files.entries())
    if(file.ok) blobs[i] = new Promise((resolve) => { resolve(file.blob()); })
  
  blobs = await Promise.all(blobs)
  for (let [i, blob] of blobs.entries()){
    if(!blob) continue;
    
    if (isSafari || isMSEdge) files[i] = blob;
    else files[i] = new File([blob], 'file_' + i, { type: blob.type });
    blobs[i] = URL.createObjectURL(blob);
  }
  
  if (request.files != blobs.filter(blob => blob != undefined).length) console.error('Uploaded file/s not found.');
  setUploadEditor(blobs); 
}

$(function() {
  $(document).tooltip({
    content: function() {
      return $(this).prop('title');
    }
  });
})
