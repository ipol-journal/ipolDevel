var clientApp = clientApp || {};
var editor = editor || {};
var helpers = clientApp.helpers || {};
var upload = clientApp.upload || {};

var isSyncingLeftScroll = false;
var isSyncingRightScroll = false;


// Print editor pannel.
editor.printEditor = function() {
  $("#inputEditorContainer").load("editor.html", function() {
    var editorBlobs;
    if (helpers.getOrigin() == "demo") editorBlobs = helpers.getFromStorage("demoSet");
    else editorBlobs = clientApp.upload.getUploadedFiles();
    
    printBlobSet(editorBlobs);
  });
};

function printBlobSet(editorBlobs) {
  $(".editor-container").removeClass("di-none");
  var demoInfo = helpers.getFromStorage("demoInfo");
  var blobs = Object.keys(editorBlobs);

  printBlobsetList(editorBlobs, demoInfo, blobs);
  
  var $blob = $("#editor-blob-left");
  var blobType = editorBlobs[blobs[0]].format;
  $('#left-container').printEditorBlob(blobType, editorBlobs[blobs[0]].blob, "left");
  $('#right-container').printEditorBlob(blobType, editorBlobs[blobs[0]].blob, "right");
  
  // If there are blobs other than images, dont load zoom and crop
  if (areAllImages(editorBlobs)) {
    $("#zoom-container").removeClass('di-none');
    if (blobs.length > 1) loadMultiBlobControlls(editorBlobs[blobs[0]].blob);
    else loadSingleBlobControlls($blob);
  }
  
  helpers.addToStorage("selectedInput-right", {
    text: "editor-input-right-0",
    src: Object.keys(editorBlobs)[0],
    format: blobType
  });
  helpers.addToStorage("selectedInput-left", {
    text: "editor-input-left-0",
    src: Object.keys(editorBlobs)[0],
    format: blobType
  });
  $(".editor-input-left-0").addClass("editor-input-selected");
  $(".editor-input-right-0").addClass("editor-input-selected");
  
  addScrollingEvents();
  
  $("#left-container").attachDragger("left");
  $("#right-container").attachDragger("right");
};

// Print the chosen set blob list
function printBlobsetList(editorBlobs, demoInfo, blobs) {
  for (let i = 0; i < blobs.length; i++) {
    $("<span class=editor-input-left-" + i + ">" + demoInfo.inputs[i].description + "</span><br>").insertBefore(".zoom-container");
    $(".blobsList-right").append("<span class=editor-input-right-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
    $(".editor-input-left-" + i).addClass('editor-input');
    $(".editor-input-right-" + i).addClass('editor-input');
    loadInputEvents(i, "left", editorBlobs);
    loadInputEvents(i, "right", editorBlobs);
  }
}

// Single blob sets controlls
function loadSingleBlobControlls($img) {
  $(".blobsList-left").append("<br><input type=checkbox id=crop-btn>Crop")
  $img.cropper({
    viewMode: 1,
    autoCrop: false,
    dragMode: 'move',
    wheelZoomRatio: 0.2,
    toggleDragModeOnDblclick: false
  });
  addCropEvent();
  singleBlobZoomController();
}

// Multiple blob sets controlls
function loadMultiBlobControlls(blob) {
  // $("#editor-blob-right").attr("src", blob);
  $(".blobsList-left").append("<br><input type=checkbox id=compare-btn>Compare");
  multiBlobZoomController();
  addCompareEvent();
}

function areAllImages(editorBlobs) {
  var blobs = Object.keys(editorBlobs);
  for (var i = 0; i < blobs.length; i++) {
    if (editorBlobs[blobs[i]].format != "image") return false;
  }
  return true;
}

$.fn.printEditorBlob = function(blobType, blobSrc, side) {
  if (blobType == 'image') {
    $(this).append('<img src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage draggable=false>');
    $("#editor-blob-left").css('width', 'auto');
    $("#editor-blob-left").css('height', 'auto');
  } else if (blobType == 'video') {
    $(this).append('<video src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage controls></video>');
  } else if (blobType == 'audio') {
    $(this).append('<audio src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage controls></audio>');
  }
}

$.fn.replaceElement = function(blobType, blobSrc, side) {
  if (blobType == 'image') {
    $('#editor-blob-' + side).replaceWith('<img src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage draggable=false>');
  } else if (blobType == 'video') {
    $('#editor-blob-' + side).replaceWith('<video src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage controls></video>');
  } else if (blobType == 'audio') {
    $('#editor-blob-' + side).replaceWith('<audio src=' + blobSrc + ' id=editor-blob-' + side + ' class=blobEditorImage controls></audio>');
  }
}

// Drag editor image mouse events
$.fn.attachDragger = function(side){
  var attachment = false, lastPosition, position, difference;
  $("#" + side + "-container").on("mousedown mouseup mousemove",function(e){
    if( e.type == "mousedown" ) attachment = true, lastPosition = [e.clientX, e.clientY];
    if( e.type == "mouseup" ) attachment = false;
    if( e.type == "mousemove" && attachment == true ){
      position = [e.clientX, e.clientY];
      difference = [ (position[0]-lastPosition[0]), (position[1]-lastPosition[1]) ];
      $(this).scrollLeft( $(this).scrollLeft() - difference[0] );
      $(this).scrollTop( $(this).scrollTop() - difference[1] );
      lastPosition = [e.clientX, e.clientY];
    }
  });
  $(window).on("mouseup", function(){
    attachment = false;
  });
}

function addCropEvent() {
  $("#crop-btn").change(function() {
    if($("#crop-btn").is(":checked")) {
      $("#editor-blob-left").cropper("crop");
    } else {
      $("#editor-blob-left").cropper("clear");
    }
  });
}

// Single blob zoom with cropper
function singleBlobZoomController () {
  $("#zoom-select").change(function() {
    var $img = $("#editor-blob-left");
    var zoomValue = $("#zoom-select").val() || 1;
    $img.cropper('zoomTo', zoomValue);
  });
}

// Zoom controller for multime blob sets
function multiBlobZoomController() {
  $("#zoom-select").change(function() {
    changeImageZoom("left");
    changeImageZoom("right");
  });
}

// Change zoom value for editor images
function changeImageZoom(side) {
  var zoomValue = $("#zoom-select").val();
  var element = $("#editor-blob-" + side);
  if (element[0].naturalHeight || element[0].naturalWidth) {
    sideWidth = element[0].naturalWidth * zoomValue;
    sideHeight = element[0].naturalHeight * zoomValue;
    $("#editor-blob-" + side).css({'width': sideWidth, 'height' : sideHeight});
  }
}

function addCompareEvent() {
  $("#compare-btn").change(function() {
    if($("#compare-btn").is(":checked")) $(".image-container").css({"flex-basis": "50%"});
    else $(".image-container").css({"flex-basis": ""});
    $(".editor-container").toggleClass("space-between");
    $(".blobsList-right").toggleClass("di-inline");
    $("#right-container").toggleClass("di-none");
    $("#right-container").toggleClass("di-inline");
    setImageContainerScroll("right");
  });
}

function addScrollingEvents() {
  var isSyncingLeftScroll = false;
  var isSyncingRightScroll = false;
  var leftDiv = document.getElementById('left-container');
  var rightDiv = document.getElementById('right-container');
  
  leftDiv.onscroll = function() {
    if (!isSyncingLeftScroll) {
      isSyncingRightScroll = true;
      rightDiv.scrollTop = this.scrollTop;
      rightDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingLeftScroll = false;
  }
  
  rightDiv.onscroll = function() {
    if (!isSyncingRightScroll) {
      isSyncingLeftScroll = true;
      leftDiv.scrollTop = this.scrollTop;
      leftDiv.scrollLeft = this.scrollLeft;
    }
    isSyncingRightScroll = false;
  }
}

function setImageContainerScroll(side){
  var imageContainer = document.getElementById(side + '-container');
  if(side == "right") var opositeImageContainer = document.getElementById('left-container');
  else var opositeImageContainer = document.getElementById('right-container');
  imageContainer.scrollTop = opositeImageContainer.scrollTop;
  imageContainer.scrollLeft = opositeImageContainer.scrollLeft;
}

// Initialize input mouseover, mouseout and click event to switch input image.
function loadInputEvents(index, side, editorBlobs) {
  var htmlImage = $("#editor-blob-" + side);
  var htmlSelector = $(".editor-input-" + side + "-" + index);
  
  htmlSelector.on('mouseover', function() {
    htmlImage.replaceElement(editorBlobs[index].format, editorBlobs[index].blob, side);
    if (editorBlobs[index].format == 'image') {
      changeImageZoom(side);
      setImageContainerScroll(side);
    }
  });
  htmlSelector.on('mouseout', function() {
    var inputName = helpers.getFromStorage("selectedInput-" + side);
    htmlImage.replaceElement(editorBlobs[inputName.src].format, editorBlobs[inputName.src].blob, side);
    if (editorBlobs[inputName.src].format == 'image') {
      changeImageZoom(side);
      setImageContainerScroll(side);
    }
  });
  htmlSelector.on('click', function() {
    var selectedInput = helpers.getFromStorage("selectedInput-" + side)
    $("." + selectedInput.text).removeClass('editor-input-selected');
    htmlSelector.addClass("editor-input-selected");
    htmlImage.replaceElement(editorBlobs[index].format, editorBlobs[index].blob, side);
    helpers.addToStorage("selectedInput-" + side, {
      text: "editor-input-" + side + "-" + index,
      src: Object.keys(editorBlobs)[index],
      format: editorBlobs[index].format
    });
    if (editorBlobs[index].format == 'image') {
      changeImageZoom(side);
      setImageContainerScroll(side);
    }
  });
}