var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var input = input || {};
var upload = upload || {};
var editor = editor || {};

var demo_sets = {};

// Print in the web Interface the sets.
input.printSets = function(sets) {
  demo_sets = sets;
  for (var i = 0; i < sets.length; i++) {
    var set = sets[i].blobs;
    var blobs = Object.keys(set);
    var name = sets[i].name;
    $(".setContainer").append("<div class=blobSet_" + i + "></div>")
      .append("<div class=blobSet-body-" + i + " id=" + name + "></div>");
    var blobSet = $(".blobSet-body-" + i);
    var blobSetArray = [];

    addSetClickEvent(blobSet, i);

    blobSetArray += "<img src=" + set[blobs[0]].thumbnail + ">"; // first photo
    if (blobs.length == 3) { // Middle photo (3 photos)
      blobSetArray += "<img src=" + set[blobs[1]].thumbnail + ">";
    }
    if (blobs.length >= 4) { // +3 photo set. ···
      blobSetArray += "<span>···</span>";
    }
    if (blobs.length > 1) { // +1 photo. last photo.
      blobSetArray += "<img src=" + set[blobs[blobs.length - 1]].thumbnail + ">";
    }
    blobSet.html(blobSetArray);
    $(".blobSet_" + i).append($(".blobSet-body-" + i));
    if (blobs.length == 1) {
      $(".blobSet_" + i).append("<span class=blobTitle>" + set[blobs].title + "</span>");
    } else {
      $(".blobSet_" + i).append("<span class=blobTitle>" + sets[i].name + "</span>");
    }
    $(".blobSet_" + i).addClass("text-center");
  }

  var setsContainer = document.getElementById("sets");
  var isChrome = !!window.chrome && !!window.chrome.webstore;
  var isFirefox = typeof InstallTrigger !== 'undefined';
  var isSafari = /constructor/i.test(window.HTMLElement) || (function(p) {
    return p.toString() === "[object SafariRemoteNotification]";
  })(!window['safari'] || safari.pushNotification);
  if (isFirefox) {
    setsContainer.addEventListener("DOMMouseScroll", scrollHorizontally, false);
  }
}

input.printInputInformationIcon = function(ddl_general) {
  checkInputDescriptionIconVisibility(ddl_general);
  $('#inputs-description').addDescription(ddl_general.input_description);
}

function scrollHorizontally(e) {
  e = window.event || e;
  if (e.deltaY) deltaValue = e.deltaY;
  else deltaValue = e.wheelDelta;
  var delta = Math.max(-1, Math.min(1, (deltaValue || -e.detail)));
  this.scrollLeft -= (delta * 70);
  e.preventDefault();
}

function addSetClickEvent(blobSet, index) {
  blobSet.addClass("blobSet")
    .click(function() {
      setEditor(index, null);
      hideStatusContainer();
    });
}

function setEditor(index, crop_info) {
  var blobs = demo_sets[index].blobs;
  var id_blobs = [];
  for (let i = 0; i < Object.keys(blobs).length; i++) {
    id_blobs.push(blobs[Object.keys(blobs)[i]].id);
  }
  helpers.addToStorage("demoSet", blobs);
  helpers.addToStorage("setId", parseInt(index));
  helpers.addToStorage("id_blobs", {
    "id_blobs": id_blobs
  });
  helpers.setOrigin("blobSet");
  editor.printEditor(crop_info);
}

function setUploadEditor(files_count, blobs, crop_info) {
  if (files_count == blobs.length) {
    for (let i = 0; i < files.length; i++) {
      uploadedFiles[i] = {
        blob: blobs[i],
        format: "image",
        thumbnail: ""
      };
    }
    helpers.setOrigin("upload");
    editor.printEditor(crop_info);
  }
}

$.fn.addDescription = function(description) {
  if (!description) return;
  var text = typeof description != 'string' ? description.join('') : description;
  if (description) $(this).attr('title', text);
}

function checkInputDescriptionIconVisibility(ddl_general) {
  if (ddl_general.input_description != undefined) $('#inputs-description').removeClass('di-none');
}
