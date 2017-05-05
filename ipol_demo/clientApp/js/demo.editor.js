var clientApp = clientApp || {};
var editor = editor || {};
var helpers = clientApp.helpers || {};
var upload = clientApp.upload || {};

var isSyncingLeftScroll = false;
var isSyncingRightScroll = false;


// Print editor pannel.
editor.printEditor = function() {
  $("#inputEditorContainer").load("editor.html", function() {
    printBlobs();
  });
};

// Print blobs or uploads depends on Origin variable.
function printBlobs() {
  var editorBlobs;
  if (helpers.getOrigin() == "demo") editorBlobs = helpers.getFromStorage("demoSet");
  else editorBlobs = clientApp.upload.getUploadedFiles();

  printBlobSet(editorBlobs);
};

function printBlobSet(editorBlobs) {
  $(".editor-container").removeClass("di-none");
  var demoInfo = helpers.getFromStorage("demoInfo");
  var blobs = Object.keys(editorBlobs);
  for (let i = 0; i < blobs.length; i++) {
    $("<span class=editor-input-left-" + i + ">" + demoInfo.inputs[i].description + "</span><br>").insertBefore(".zoom-container");
    $(".blobsList-right").append("<span class=editor-input-right-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
    $(".editor-input-left-" + i).addClass('editor-input');
    $(".editor-input-right-" + i).addClass('editor-input');
    loadInputEvents(i, "left", editorBlobs[blobs[i]].blob, editorBlobs);
    loadInputEvents(i, "right", editorBlobs[blobs[i]].blob, editorBlobs);
  }

  if (blobs.length > 1) $(".blobsList-left").append("<br><input type=checkbox id=compare-btn>Compare");
  $(".editor-image-left").attr("src", editorBlobs[blobs[0]].blob);
  $(".editor-image-right").attr("src", editorBlobs[blobs[0]].blob);

  helpers.addToStorage("selectedInput-right", {
    text: "editor-input-right-0",
    src: Object.keys(editorBlobs)[0]
  });
  helpers.addToStorage("selectedInput-left", {
    text: "editor-input-left-0",
    src: Object.keys(editorBlobs)[0]
  });

  $(".editor-input-right-0").addClass("editor-input-selected");
  $(".editor-input-left-0").addClass("editor-input-selected");

  addCompareEvent();
  addScrollingEvents();
  zoomController();
};

// Add zoom to editor images
function zoomController () {
  $("#zoom-select").change(function() {
    changeImageZoom("left");
    changeImageZoom("right");
  });
}
function changeImageZoom(side) {
  var zoomValue = $("#zoom-select").val();
  var element = document.getElementsByClassName("editor-image-" + side)[0];
  sideWidth = element.naturalWidth * zoomValue;
  sideHeight = element.naturalHeight * zoomValue;
  $(".editor-image-" + side).css({'width': sideWidth, 'height' : sideHeight});
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
function loadInputEvents(index, side, image, editorBlobs) {
  var htmlImage = $(".editor-image-" + side);
  var htmlSelector = $(".editor-input-" + side + "-" + index);

  htmlSelector.on('mouseover', function() {
    htmlImage.attr("src", image);
    changeImageZoom(side);
    setImageContainerScroll(side);
  });
  htmlSelector.on('mouseout', function() {
    var inputName = helpers.getFromStorage("selectedInput-" + side);
    htmlImage.attr("src", editorBlobs[inputName.src].blob);
  });
  htmlSelector.on('click', function() {
    var selectedInput = helpers.getFromStorage("selectedInput-" + side)
    $("." + selectedInput.text).removeClass('editor-input-selected');
    htmlSelector.addClass("editor-input-selected");
    htmlImage.attr("src", helpers.addToStorage("selectedInput-" + side, {
      text: "editor-input-" + side + "-" + index,
      src: Object.keys(editorBlobs)[index]
    }));
    changeImageZoom(side);
    setImageContainerScroll(side);
  });
}
