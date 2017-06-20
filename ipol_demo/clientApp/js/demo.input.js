var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};
var input = input || {};
var upload = upload || {};
var editor = editor || {};

// Print in the web Interface the sets.
input.printSets = function(sets) {
  for (var i = 0; i < sets.length; i++) {
    var set = sets[i].blobs;
    var blobs = Object.keys(set);
    var name = sets[i].name;
    $(".setContainer").append("<div class=blobSet_" + i + "></div>")
      .append("<div class=blobSet-body-" + i + " id=" + name + "></div>");
    var blobSet = $(".blobSet-body-" + i);
    var blobSetArray = [];

    addSetClickEvent(blobSet, set);

    blobSetArray += "<img src=" + set[0].thumbnail + ">"; // first photo
    if (blobs.length == 3) { // Middle photo (3 photos)
      blobSetArray += "<img src=" + set[1].thumbnail + ">";
    }
    if (blobs.length >= 4) { // +3 photo set. ···
      blobSetArray += "<span>···</span>";
    }
    if (blobs.length > 1) { // +1 photo. last photo.
      blobSetArray += "<img src=" + set[blobs.length - 1].thumbnail + ">";
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
  } else {
    setsContainer.addEventListener("mousewheel", MouseWheelHandler(), false);
  }
}

input.printInputInformationIcon = function(ddl_general){
  checkInputDescriptionIconVisibility(ddl_general);
  addInputDescriptionTooltips(ddl_general);
}

function scrollHorizontally(e) {
  e = window.event || e;
  if (e.deltaY) deltaValue = e.deltaY;
  else deltaValue = e.wheelDelta;
  var delta = Math.max(-1, Math.min(1, (deltaValue || -e.detail)));
  this.scrollLeft -= (delta * 70);
  e.preventDefault();
}

function MouseWheelHandler() {
  return function(e) {
    // cross-browser wheel delta
    var e = window.event || e;
    // Get delta value from deltaY instead of wheelDelta for trackpad support.
    var deltaValue;
    if (e.deltaY) deltaValue = e.deltaY;
    else deltaValue = e.wheelDelta;
    var delta = Math.max(-1, Math.min(1, (deltaValue || -e.detail)));
    if (delta < 0) this.scrollLeft += 20;
    else this.scrollLeft -= 20;

    e.preventDefault();
    return false;
  }
}

function addSetClickEvent(blobSet, blobs) {
  blobSet.addClass("blobSet")
    .click(function() {
      helpers.addToStorage("demoSet", blobs);
      helpers.setOrigin("blobSet");
      editor.printEditor();
    });
}

function addInputDescriptionTooltips(ddl_general) {
  if (ddl_general.input_description)
    $('#inputs-description').attr('title', getConcatDescription(ddl_general.input_description));
}

function checkInputDescriptionIconVisibility(ddl_general) {
  if (ddl_general.input_description != undefined) $('#inputs-description').removeClass('di-none');
}

function getConcatDescription(inputDescription) {
  var description = "";
  for (let i = 0; i < inputDescription.length; i++) {
    description += inputDescription[i];
  }
  return description;
}
