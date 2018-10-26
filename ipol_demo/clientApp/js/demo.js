"use strict"

var demo_id;
var demoInfo, experiment;
var files = [];

// Initial trigger.
$(document).ready(function() {
  demo_id = getDemoId();

  // Workaround: use the old interface only for inpainting demos
  if ($.inArray(parseInt(demo_id), [189, 198, 228, 333330030001]) != -1) {
    // Move to the old interface
    window.location = "/demo/clientAppOld/demo.html?id=" + demo_id;
  } 

  var isNumber = (/^\d+$/.test(demo_id))
  if (demo_id && isNumber){
    $("#header").load("header.html");
    $("#inputEditorContainer").load("editor.html");
    $("#parameters").load("parameters.html");
    $("#footer").load("footer.html");
    sessionStorage.clear();
    
    $('#archiveTab').attr('href', 'archive.html?id=' + demo_id);
    
    getBlobSets();
    getDemoinfo();
  } else{ 
    alert("Wrong demo id: " + demo_id);
    window.location = '/demo';
  }
});

window.onpopstate = function() {
  hideStatusContainer();
  $("#inputEditorContainer").empty();

  if (getExecutionKey()) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getExecutionKey());
  else if (getArchiveExperimentId()) loadExecution("/api/archive/get_experiment?experiment_id=" + getArchiveExperimentId());
  else {
    $('.results').addClass('di-none');
    $('.results-container').empty();
  }
};

// Get Demo_Id from URL.
function getDemoId() {
  return getParameterByName('id');
}

// Get Key from URL.
function getExecutionKey() {
  return getParameterByName('key');
}

function getArchiveExperimentId(){
  return getParameterByName('archive');
}

function getBlobSets() {
  helpers.getFromAPI("/api/blobs/get_blobs?demo_id=" + demo_id, function(blobs) {
    console.log("get_globs", blobs);
    if (blobs.status != "OK") {
      alert("Wrong demo id: " + demo_id);
      window.location = '/demo';
    }
    helpers.addToStorage("blobs", blobs.sets);
    input.printSets(blobs.sets);
    if (getExecutionKey()) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getExecutionKey());
    if (getArchiveExperimentId()) loadExecution("/api/archive/get_experiment?experiment_id=" + getArchiveExperimentId());
  });
}

function getDemoinfo() {
  helpers.getFromAPI("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id, function(payload) {
    if (payload.status != "OK") {
      alert("Wrong demo id: " + demo_id);
      window.location = '/demo';
    }
    var response = helpers.getJSON(payload.last_demodescription.ddl);
    demoInfo = response;
    console.log("get_interface_ddl", response);
    if(response.general.description) displayDemoDescription()
    displayInputHeaders(response);
    printDemoHeader(response);
    helpers.addToStorage("demoInfo", response);
    parameters.printParameters();
    if (demoInfo.general.custom_js) loadDemoExtrasJS()
    if (getExecutionKey()) loadExecution("/api/core/load_execution?demo_id=" + demo_id + '&key=' + getExecutionKey());
    if (getArchiveExperimentId()) loadExecution("/api/archive/get_experiment?experiment_id=" + getArchiveExperimentId());
  });
}

function displayDemoDescription(){
  $(".citation").after('<div class="container description-container"></div>');
  $(".description-container").append('<h1 class="container-title m-y-5">Description</h1>');
  $('.description-container').append('<p class=description > ' + demoInfo.general.description + '</p>');
}

function loadDemoExtrasJS() {
  var url = demoInfo.general.custom_js
  $.getScript(url)
    .fail(function () {
      console.error("Could not load the script: " + url)
    })
}

function displayInputHeaders(ddl) {
  if (ddl.inputs && ddl.inputs.length != 0) {
    $(".inputContainer").removeClass('di-none');
    $("#inputEditorContainer").removeClass('di-none');
    input.printInputInformationIcon(ddl.general);
    upload.printUploads(ddl.inputs);
  }
}

function printDemoHeader(response) {
  $("#pageTitle").html(response.general.demo_title);
  $(".citation").html("<span>Please cite <a id=citation-link>the reference article</a> if you publish results obtained with this online demo.</span>");
  $("#citation-link").attr('href', response.general.xlink_article);
  $("#articleTab").attr('href', response.general.xlink_article);
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

/* 
This implements the mechanism that allows to reconstruct an experiment from the temporal folder or archive, depending on the url.
*/
function loadExecution(url){
    if (helpers.getFromStorage("demoInfo") != null && helpers.getFromStorage("blobs") != null) {
      $.getJSON(url, function(data) {
        if (data.status === "OK") {
          console.log(data);
          experiment = data.experiment;
          var execution = JSON.parse(data.execution || experiment.execution);
          console.log(execution.request)
          var request = execution != null ? execution.request : null;
          
          renderExperiment(request, execution.response);
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
  if (run_request.origin == "blobSet") setEditor(run_request.setId, run_request.crop_info)
  if (run_request.origin == "upload") setFiles(run_request, execution_response)
  if (run_request.private_mode) $('#privateSwitch').prop('checked', true);
  results.draw(execution_response);
}

function setFiles(request, response) {
  var blobs = [];
  var isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
  var isMSEdge = window.navigator.userAgent.indexOf("Edge") > -1;

  for (let i = 0; i < request.files; i++) {
    let xhr = new XMLHttpRequest();
    var file_url = getFileURL('input_' + i + demoInfo.inputs[i].ext);
    xhr.open("GET", file_url);
    xhr.responseType = "blob";
    xhr.onload = function() {
      if(xhr.status == 404){
        console.log("Uploaded file not found.");
        files = [];
        blobs = [];
        return;
      }
      let blob = xhr.response;

      // Safari and MS Edge use blob instead of File object due to support issues.
      if(isSafari || isMSEdge) files.push(blob);
      else{
        let myFile = new File([blob], "file_" + i, {
          type: blob.type
        });
        files.push(myFile);
      } 

      let reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = function() {
        blobs[i] = (reader.result);
        setUploadEditor(request.files, blobs);
      }
    }
    xhr.send();
  }
}

$(function() {
  $(document).tooltip({
    content: function() {
      return $(this).prop('title');
    }
  });
});

