"use strict"

var demo_id, ddl, experiment, work_url, files = [];

$(document).ready(function() {
  demo_id = getParameterFromURL('id');

  // Workaround: use the old interface only for inpainting demos
  if ($.inArray(parseInt(demo_id), [189, 198, 228, 333330030001]) != -1)
    window.location = "/demo/clientAppOld/demo.html?id=" + demo_id; // Move to the old interface

  var demo_id_is_number = (/^\d+$/.test(demo_id));
  if (demo_id_is_number) {
    $("#header").load("header.html");
    $("#inputEditorContainer").load("editor.html");
    $("#parameters").load("parameters.html");
    $("#footer").load("footer.html");
    sessionStorage.clear();
    
    $('#archiveTab').attr('href', 'archive.html?id=' + demo_id);
    
    getBlobSets();
    getDDL();
  } else
    showWrongDemoIdError();
})

window.onpopstate = function() {
  hideStatusContainer();
  $("#inputEditorContainer").empty();

  if (getParameterFromURL('key')) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getParameterFromURL('key'));
  else if (getParameterFromURL('archive')) loadExecution("/api/archive/get_experiment?experiment_id=" + getParameterFromURL('archive'));
  else {
    $('.results').addClass('di-none');
    $('.results-container').empty();
  }
}

function getBlobSets() {
  helpers.getFromAPI("/api/blobs/get_blobs?demo_id=" + demo_id, function(blobs) {
    console.log("Blobs", blobs);
    if (blobs.status != "OK") showWrongDemoIdError();
    
    helpers.addToStorage("blobs", blobs.sets);
    input.printSets(blobs.sets);
    if (getParameterFromURL('key')) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getParameterFromURL('key'));
    if (getParameterFromURL('archive')) loadExecution("/api/archive/get_experiment?experiment_id=" + getParameterFromURL('archive'));
  });
}

function getDDL() {
  helpers.getFromAPI("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id, function(payload) {
    if (payload.status != "OK") showWrongDemoIdError();
    ddl = payload.last_demodescription.ddl;
    loadDemoPage();
    if (ddl.general.custom_js) loadDemoExtrasJS();
    if (getParameterFromURL('key')) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getParameterFromURL('key'));
    if (getParameterFromURL('archive')) loadExecution("/api/archive/get_experiment?experiment_id=" + getParameterFromURL('archive'));
  });
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
function loadExecution(url){
  if (ddl != null && helpers.getFromStorage("blobs") != null) { 
    $.getJSON(url, function(data) {
      if (data.status === "OK") {
        if(getParameterFromURL("archive")){ //Archive reconstruction
          experiment = data.experiment;
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
    });
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