var clientApp = clientApp || {};
var editor = editor || {};
var helpers = clientApp.helpers || {};

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
  if (helpers.getOrigin() == "demo") printBlobSet();
  else list = printUploads();
};

function printBlobSet() {
  $(".editor-container").removeClass("di-none");
  var selectedSet = helpers.getFromStorage("demoSet");
  var demoInfo = helpers.getFromStorage("demoInfo");
  var blobs = Object.keys(selectedSet);
  for (let i = 0; i < blobs.length; i++) {
    $(".blobsList-left").append("<span class=editor-input-left-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
    $(".blobsList-right").append("<span class=editor-input-right-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
    $(".editor-input-left-" + i).addClass('editor-input');
    $(".editor-input-right-" + i).addClass('editor-input');
    loadInputEvents(i, "left", selectedSet[blobs[i]].blob);
    loadInputEvents(i, "right", selectedSet[blobs[i]].blob);
  }

  if(blobs.length > 1)$(".blobsList-left").append("<br><input type=checkbox id=compare-btn>Compare");
  $(".editor-image-left").attr("src", selectedSet[blobs[0]].blob);
  $(".editor-image-right").attr("src", selectedSet[blobs[0]].blob);
  helpers.addToStorage("selectedInput-right", {text: "editor-input-right-0", src: selectedSet[blobs[0]].blob});
  helpers.addToStorage("selectedInput-left", {text: "editor-input-left-0", src: selectedSet[blobs[0]].blob});
  $(".editor-input-right-0").addClass("editor-input-selected");
  $(".editor-input-left-0").addClass("editor-input-selected");

  addCompareEvent();
  addScrollingEvents();

};
// Print uploads list and set image src with hover and click events.
function printUploads() {
  $(".editor-container").removeClass("di-none");
  var demoInfo = helpers.getFromStorage("demoInfo");
  var upload;
  var images = [];
  for (var i = 0; i < demoInfo.inputs.length; i++) {
    upload = helpers.getFromStorage(demoInfo.inputs[i].description); // Revisar
    if (upload) {
      images.push({
        "name": demoInfo.inputs[i].description,
        "src": upload
      });
      $(".blobsList-left").append("<span class=editor-input-left-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
      $(".blobsList-right").append("<span class=editor-input-right-" + i + ">" + demoInfo.inputs[i].description + "</span><br>");
      $(".editor-input-left-" + i).addClass('editor-input');
      $(".editor-input-right-" + i).addClass('editor-input');
      loadInputEvents(i, "left", upload);
      loadInputEvents(i, "right", upload);
    };
  };
  if(images.length > 1)$(".blobsList-left").append("<br><input type=checkbox id=compare-btn>Compare");
  $(".editor-image-left").attr("src", images[0].src);
  $(".editor-image-right").attr("src", images[0].src);
  helpers.addToStorage("selectedInput-right", {text: "editor-input-right-0", src: images[0].src});
  helpers.addToStorage("selectedInput-left", {text: "editor-input-left-0", src: images[0].src});
  $(".editor-input-right-0").addClass("editor-input-selected");
  $(".editor-input-left-0").addClass("editor-input-selected");

  addCompareEvent();
  addScrollingEvents();
};

function addCompareEvent() {
  $("#compare-btn").change(function() {
    $(".image-wrapper").toggleClass("image-grid-1");
    $(".image-wrapper").toggleClass("image-grid-2");
    $(".blobsList-right").toggleClass("di-inline");
    $("#right-container").toggleClass("di-none");
    $("#right-container").toggleClass("di-inline");
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

// Initialize input mouseover, mouseout and click event to switch input image.
function loadInputEvents(index, side, image) {
  var element = $(".editor-image-" + side);
  var selector = $(".editor-input-" + side + "-" + index);
  selector.on('mouseover', function() {
    element.attr("src", image);
  });
  selector.on('mouseout', function() {
    element.attr("src", helpers.getFromStorage("selectedInput-" + side).src);
  });
  selector.on('click', function() {
    var selectedInput = helpers.getFromStorage("selectedInput-" + side)
    $("." + selectedInput.text).removeClass('editor-input-selected');
    selector.addClass("editor-input-selected");
    element.attr("src", helpers.addToStorage("selectedInput-" + side, {text: "editor-input-" + side + "-" + index, src: image}));
  });
}
