"use strict"
var demo_id;

// Initial trigger.
$(document).ready(function() {
  $("#header").load("header.html");
  $("#inputEditorContainer").load("editor.html");
  $("#parameters").load("parameters.html");
  $("#footer").load("footer.html");
  clearStorage();
  demo_id = getDemoId();
  $('#archiveTab').attr('href', '/demo/clientApp/archive.html?id=' + demo_id);
  getBlobSets();
  getDemoinfo();
});

function getBlobSets() {
  helpers.getFromAPI("/api/blobs/get_blobs?demo_id=" + demo_id, function(blobs) {
    input.printSets(blobs.sets);
    helpers.addToStorage("blobs", blobs.sets);
    console.log("get_globs", blobs);
  });
}

function getDemoinfo() {
  helpers.getFromAPI("/api/demoinfo/get_interface_ddl?demo_id=" + demo_id, function(payload) {
    var response = helpers.getJSON(payload.last_demodescription.ddl);
    displayInputHeaders(response);
    printDemoHeader(response);
    helpers.addToStorage("demoInfo", response);
    parameters.printParameters();
    console.log("get_interface_ddl", response);
  });
}

function displayInputHeaders(ddl){
  if(ddl.inputs.length != 0){
    $(".inputContainer").removeClass('di-none');
    $("#inputEditorContainer").removeClass('di-none');
    input.printInputInformationIcon(ddl.general);
    upload.printUploads(ddl.inputs);
  }
}

function printDemoHeader(response){
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

// Clear all sessionStorage.
function clearStorage() {
  Object.keys(sessionStorage).forEach(function(key) {
    sessionStorage.removeItem(key);
  });
}

$(function() {
  $(document).tooltip({
    content: function() {
      return $(this).prop('title');
    }
  });
});
