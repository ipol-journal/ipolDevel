var clientApp = clientApp || {};
var editor = editor || {};
var helpers = clientApp.helpers || {};
var upload = clientApp.upload || {};
var zoomController = zoomController || {};
var scrollController = scrollController || {};

var editorBlobs;
var crop_info;

// Print editor pannel.
editor.printEditor = function(crop) {
  $("#inputEditorContainer").load("editor.html", function() {
    if (helpers.getOrigin() == "blobSet")
      editorBlobs = helpers.getFromStorage("demoSet");
    else editorBlobs = clientApp.upload.getUploadedFiles();
    crop_info = crop;
    printEditorPanel();
  });
};

function printEditorPanel() {
  $(".editor-container").removeClass("di-none");
  var demoInfo = helpers.getFromStorage("demoInfo");
  var blobs = Object.keys(editorBlobs);

  printBlobsetList(demoInfo, blobs);

  $("#left-container").printEditorBlob(editorBlobs[blobs[0]], "left");
  $("#right-container").printEditorBlob(editorBlobs[blobs[0]], "right");
  var $blob = $("#editor-blob-left");

  if (areAllImages()) $("#zoom-container").removeClass("di-none");
  if (blobs.length > 1) loadMultiBlobControls(editorBlobs[blobs[0]].blob);
  else if (blobs.length == 1 && (editorBlobs[blobs[0]].format == "image" || editorBlobs[blobs[0]].vr)) loadSingleBlobControls($blob);

  var blobType = editorBlobs[blobs[0]].format;
  saveSelectedInput("right", blobs[0]);
  saveSelectedInput("left", blobs[0]);

  $(".editor-input-left-0").addClass("editor-input-selected");
  $(".editor-input-right-0").addClass("editor-input-selected");

  scrollController.addScrollingEvents();

  $("#left-container").attachDragger("left");
  $("#right-container").attachDragger("right");
}

function saveSelectedInput(side, index) {
  blobsKeys = Object.keys(editorBlobs);
  helpers.addToStorage("selectedInput-" + side, {
    text: "editor-input-" + side + "-" + index,
    src: blobsKeys[blobsKeys.indexOf(index)],
    format: editorBlobs[index].format
  });
}

// Print the chosen set blob list
function printBlobsetList(demoInfo, blobs) {
  for (let i = 0; i < blobs.length; i++) {
    $(".inputListContainerLeft").append(
      "<span class=editor-input-left-" +
        i +
        ">" +
        demoInfo.inputs[i].description +
        "</span>"
    );
    $(".editor-input-left-" + i).addClass("editor-input");
    $(".editor-input-left-" + i).loadInputEvents(
      Object.keys(editorBlobs)[i],
      "left"
    );
    $(".inputListContainerRight").append(
      "<span class=editor-input-right-" +
        i +
        ">" +
        demoInfo.inputs[i].description +
        "</span>"
    );
    $(".editor-input-right-" + i).addClass("editor-input");
    $(".editor-input-right-" + i).loadInputEvents(
      Object.keys(editorBlobs)[i],
      "right"
    );
  }
  $(".inputListContainerLeft").loadInputsContainerEvent("left");
  $(".inputListContainerRight").loadInputsContainerEvent("right");
}

// Single blob sets controls
function loadSingleBlobControls($img) {
  $(".blobsList-left").append(
    "<input type=checkbox id=crop-btn class=hand><label for=crop-btn class=hand>Crop</label>"
  );
    if (crop_info == null) {
      $img.cropper({
        viewMode: 1,
        autoCrop: false,
        dragMode: "move",
        wheelZoomRatio: 0.1,
        responsive: true,
        toggleDragModeOnDblclick: false,
        ready: setNaturalZoom
      });
    } else {
      $img.cropper({
        viewMode: 1,
        autoCrop: true,
        dragMode: "move",
        wheelZoomRatio: 0.1,
        responsive: true,
        data: crop_info,
        ready: getData,
        toggleDragModeOnDblclick: false
      });
      $("#crop-btn").prop("checked", true);
      $("#canvas-container").removeClass("di-none");
    }
  $img.on("cropmove cropstart cropend", function(e) {
    if ($("#crop-btn").prop("checked")) {
      var croppedImage = $("#left-container > img").cropper("getCroppedCanvas");
      $("#canvas-container").html($(croppedImage));
    }
  });
  $img.on("zoom", function(e) {
    if (e.ratio >= 0.25 && e.ratio <= 16) {
      let selector = "#canvas-container > canvas, .blobEditorImage, .cropper-container img";
      helpers.checkInterpolation(e.ratio, selector);
     
      $("#editor-zoom").val(e.ratio);
      $("#editor-zoom-value").html(e.ratio.toFixed(2) + "x");
      if ($("#crop-btn").prop("checked")) {
        var croppedImage = $("#left-container > img").cropper(
          "getCroppedCanvas"
        );
        $("#canvas-container").html($(croppedImage));
      }
    } else {
      e.preventDefault();
    }
  });
  addCropEvent();
  zoomController.singleBlob();
}

function setNaturalZoom(e) {
  $("#editor-blob-left").cropper('zoomTo', 1);
}

function getData(e) {
  var imgData = $("#editor-blob-left").cropper("getImageData");
  var zoom = imgData.height / imgData.naturalHeight;
  $("#editor-zoom").val(zoom);
  $("#editor-zoom-value").html(zoom.toFixed(2) + "px");
  $("#editor-blob-left").cropper('zoomTo', zoom);
}

// Multiple blob sets controls
function loadMultiBlobControls(blob) {
  $(".blobsList-left").append(
    "<input type=checkbox id=compare-btn class=hand><label for=compare-btn>Compare</label>"
  );
  zoomController.multiBlob();
  addCompareEvent();
}

// Check if all blobs are images or have visual representation (image)
function areAllImages() {
  var blobs = Object.keys(editorBlobs);
  for (var i = 0; i < blobs.length; i++) {
    if (editorBlobs[blobs[i]].format != "image" && !editorBlobs[blobs[i]].vr)
      return false;
  }
  return true;
}

$.fn.printEditorBlob = function(editorBlob, side) {
  var blobType = editorBlob.format;
  var blobSrc = editorBlob.vr ? editorBlob.vr : editorBlob.blob;
  if (blobType == "video") {
    $(this).empty();
    $(this).append(
      "<video src=" +
        blobSrc +
        " id=editor-blob-" +
        side +
        " class=blobEditorVideo controls></video>"
    );
  } else if (blobType == "audio") {
    $(this).empty();
    var audioThumbnail = editorBlob.thumbnail
      ? editorBlob.thumbnail
      : "assets/non_viewable_data.png";
    $(this).append(
      "<img src=" +
        audioThumbnail +
        " class=audioThumbnail><br><audio src=" +
        blobSrc +
        " id=editor-blob-" +
        side +
        " class=blobEditorAudio controls></audio>"
    );
  } else {
    if (isPreviousBlobImg(side)) {
      $("#editor-blob-" + side).attr("src", blobSrc);
    } else {
      $(this).empty();
      var img = "<img src=" + blobSrc + " id=editor-blob-" + side + " class=blobEditorImage draggable=false >";
      // $(this).append("<img src=" + blobSrc + " id=editor-blob-" + side + " class=blobEditorImage draggable=false >");
      $(img).appendTo($(this));
      $(img).displayImageSize();
      $("#editor-blob-left").on("error", function() {
        $(this).attr("src", "assets/non_viewable_data.png");
        $("#editor-blob-left").css({ width: "auto", height: "auto" });
      });
      $("#editor-blob-left").css({ width: "auto", height: "auto" });
    }
  }
};

function isPreviousBlobImg(side) {
  var previousBlob = document.getElementById("editor-blob-" + side);
  if (previousBlob != null && $("#editor-blob-" + side).is("img")) return true;
  return false;
}

function addCropEvent() {
  $("#crop-btn").on("click", function() {
    if ($("#crop-btn").is(":checked")) {
      $("#editor-blob-left").cropper("crop");
      var croppedImage = $("#left-container > img").cropper("getCroppedCanvas");
      $("#canvas-container").html($(croppedImage));
      $("#canvas-container").removeClass("di-none");
    } else {
      $("#canvas-container").addClass("di-none");
      $("#editor-blob-left").cropper("clear");
      $("#canvas-container").html("<div></div>");
    }
  });
}

function addCompareEvent() {
  $("#compare-btn").change(function() {
    if ($("#compare-btn").is(":checked"))
      $(".image-container").css({
        "flex-basis": "50%"
      });
    else
      $(".image-container").css({
        "flex-basis": ""
      });
    $(".editor-container").toggleClass("space-between");
    $(".blobsList-right").toggleClass("di-inline");
    $("#right-container").toggleClass("di-none");
    $("#right-container").toggleClass("di-inline");
    $(".blobsList-right").toggleClass("di-none");
  });
}

// Initialize input mouseover, mouseout and click event to switch input image.
$.fn.loadInputEvents = function(index, side) {
  var container = $("#" + side + "-container");

  $(this).on("mouseover", function() {
    container.printEditorBlob(editorBlobs[index], side);
    zoomSync(editorBlobs[index], side);
  });

  $(this).on("click", function() {
    var selectedInput = helpers.getFromStorage("selectedInput-" + side);
    $("." + selectedInput.text).removeClass("editor-input-selected");
    $(this).addClass("editor-input-selected");
    container.printEditorBlob(editorBlobs[index], side);
    saveSelectedInput(side, index);
    zoomSync(editorBlobs[index], side);
  });
};

$.fn.loadInputsContainerEvent = function(side) {
  var container = $("#" + side + "-container");
  $(this).on("mouseout", function(event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    var inputName = helpers.getFromStorage("selectedInput-" + side);
    container.printEditorBlob(editorBlobs[inputName.src], side);
    zoomSync(editorBlobs[inputName.src], side);
  });
};

function zoomSync(blob, side) {
  if (blob.format == "image") {
    zoomController.changeImageZoom(side);
  }
}

$.fn.displayImageSize = function() {
  $(this).on('load', function() {
    console.log($(this)[0].naturalHeight);
    $("#editor-image-size").html($(this)[0].naturalWidth + " x " + $(this)[0].naturalHeight);
  });
};