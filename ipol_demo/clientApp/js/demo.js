"use strict"
var demo_id;

var demoInfo;
var experiment;
var execution;
var files = [];
// Initial trigger.
$(document).ready(function() {
  demo_id = getDemoId();

  // Workaround: use the old interface only for inpainting demos
  if ($.inArray(parseInt(demo_id), [189, 198, 77777000030]) != -1) {
      // Move to the old interface
      window.location = "/demo/clientAppOld/demo.html?id=" + demo_id;
  }

  $("#header").load("header.html");
  $("#inputEditorContainer").load("editor.html");
  $("#parameters").load("parameters.html");
  $("#footer").load("footer.html");
  sessionStorage.clear();

  $('#archiveTab').attr('href', 'archive.html?id=' + demo_id);
  getBlobSets();
  getDemoinfo();
});

function getBlobSets() {
  helpers.getFromAPI("/api/blobs/get_blobs?demo_id=" + demo_id, function(blobs) {
    console.log("get_globs", blobs);
    input.printSets(blobs.sets);
    helpers.addToStorage("blobs", blobs.sets);
    if (getKey()) loadExecution(getKey());
  });
}

function getDemoinfo() {
  helpers.getFromAPI("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id, function(payload) {
    var response = helpers.getJSON(payload.last_demodescription.ddl);
    console.log("get_interface_ddl", response);
    displayInputHeaders(response);
    printDemoHeader(response);
    demoInfo = response;
    helpers.addToStorage("demoInfo", response);
    parameters.printParameters();
    if(getKey()) loadExecution(getKey());
    if(getArchiveKey()) loadArchiveExecution(getArchiveKey());
  });
}

function displayInputHeaders(ddl) {
  if (ddl.inputs.length != 0) {
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

// Get Demo_Id from URL.
function getDemoId() {
  return getParameterByName('id');
}

// Get Key from URL.
function getKey() {
  return getParameterByName('key');
}

function getArchiveKey(){
  return getParameterByName('archive');
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

function loadExecution(key) {
  if (helpers.getFromStorage("demoInfo") != null && helpers.getFromStorage("blobs") != null) {
    hideStatusContainer();  
    helpers.getFromAPI("/api/core/load_execution?demo_id=" + demo_id + '&key=' + key, function(data) {
      if (data.status == "OK") {
        var execution_json = JSON.parse(data.execution);
        var request = JSON.parse(execution_json.request);
        work_url = execution_json.response.work_url;
        
        if (!$.isEmptyObject(request.params)) parameters.setParametersValues(request.params);
        if (request.origin == "blobSet") setEditor(request.setId, request.crop_info)
        if (request.origin == "upload") setFiles(request, execution_json.response)
        if (request.private_mode) $('#privateSwitch').prop('checked', true);
        results.draw(execution_json.response);
      } else {
        alert(data.error);
        window.location.href = "demo.html?id=" + demo_id;
      }
    });
  }
}

function loadArchiveExecution(archive_id) {
  var url = "/api/core/get_experiment_from_archive?experiment_id=" + archive_id;
  $.getJSON(url, function (data) {
    if (data.response.status === "OK") {
      experiment = data.response.experiment;
      execution = JSON.parse(data.response.experiment.execution);
      work_url = execution.response.work_url;
      var request = execution != null ? JSON.parse(execution.request) : null;
      
      if (!$.isEmptyObject(request.params)) parameters.setParametersValues(request.params);
      if (request.origin == "blobSet") setEditor(request.setId, request.crop_info)
      if (request.origin == "upload") setFiles(request, execution.response)
      if (request.private_mode) $('#privateSwitch').prop('checked', true);
      results.draw(execution.response);
    } else{
      alert('Archive experiment id not found.');
      window.location.href = "demo.html?id=" + demo_id;
    }
  })
   .fail(function (err) {
      alert('Experiment load fail. Error: ' + data.err);
      window.location.href = "demo.html?id=" + demo_id;
  });
}

function setFiles(request, response) {
  var blobs = [];
  for (let i = 0; i < request.files; i++) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", getFileURL('input_' + i + demoInfo.inputs[i].ext));
    xhr.responseType = "blob";
    xhr.onload = function() {
      if(xhr.status == 404){
        console.log("Uploaded file not found.");
        files = [];
        blobs = [];
        return;
      }
      let blob = xhr.response;
      let myFile = new File([blob], "file_" + i, {
        type: blob.type
      });
      files.push(myFile);

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

window.onpopstate = function(e) {
  hideStatusContainer();
  $("#inputEditorContainer").empty();
  if (getKey()) loadExecution(getKey());
  if (getArchiveKey()) loadArchiveExecution(getArchiveKey());
  else {
    $('.results').addClass('di-none');
    $('.results-container').empty();
  }
};
