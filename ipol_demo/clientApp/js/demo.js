"use strict"
var demo_id;

var demoInfo;
var execution;
var files = [];
// Initial trigger.
$(document).ready(function() {
  $("#header").load("header.html");
  $("#inputEditorContainer").load("editor.html");
  $("#parameters").load("parameters.html");
  $("#footer").load("footer.html");
  sessionStorage.clear();
  demo_id = getDemoId();
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
    if (getKey()) loadExecution(getKey());
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
  var urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('id');
}

// Get Key from URL.
function getKey() {
  var urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('key');
}

function loadExecution(key) {
  if (helpers.getFromStorage("demoInfo") != null && helpers.getFromStorage("blobs") != null) {
    hideStatusContainer();  
    helpers.getFromAPI("/api/core/load_execution?demo_id=" + demo_id + '&key=' + key, function(payload) {
      if (payload.status == "OK") {
        var execution_json = JSON.parse(payload.execution);
        var request = JSON.parse(execution_json.request);
        if (!$.isEmptyObject(request.params)) parameters.setParametersValues(request.params);
        if (request.origin == "blobSet") setEditor(request.setId, request.crop_info)
        if (request.origin == "upload") setFiles(request, execution_json.response)
        if (request.private_mode) $('#privateSwitch').prop('checked', true);
        results.draw(execution_json.response);
      } else {
        alert(payload.error);
        window.location.href = "demo.html?id=" + demo_id;
      }
    });
  }
}

function setFiles(request, response) {
  var blobs = [];
  for (let i = 0; i < request.files; i++) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", response.work_url + 'input_' + i + demoInfo.inputs[i].ext);
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
  else {
    $('.results').addClass('di-none');
    $('.results-container').empty();
  }
};
