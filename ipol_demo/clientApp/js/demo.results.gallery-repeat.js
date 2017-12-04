var helpers = clientApp.helpers || {};

$.fn.repeat_gallery = function(result, index)  {
  if (result.visible) {
    var visible = eval(result.visible);
    if (!visible) return;
  }
  if (result.label) $(this).appendLabel(result.label);
  
  var blobListString = result.contents[0];
  var contentArray = result.contents[1];
  var repeat = getRepeat(result);
  if (typeof(contentArray) == "string") {
    contentArray = [contentArray]
  } else if (typeof(contentArray) == "object") {
    let titles = Object.keys(contentArray);
    contentArray = Object.keys(contentArray).map(function(e) {
      return contentArray[e];
    });
  }
  
  var blobsArray = getAllImages(repeat, contentArray, work_url);

  var gallerySelector = "gallery-" + index;
  $(this).append('<div class="' + gallerySelector + ' gallery-container"></div>');

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  renderRepeatBlobList(index, blobListString, gallerySelector, leftItems, 'left', repeat, blobsArray);

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append('<div class="' + blobsContainerSelector + ' blobs-wrapper"></div>');
  renderRepeatBlobList(index, blobListString, gallerySelector, rightItems, 'right', repeat, blobsArray);
  $("." + rightItems).addClass("gallery-item-list-right di-none");

  // Append both sides image containers
  var imgContainerLeft = "gallery-blobs-left-" + index;
  var imgContainerRight = "gallery-blobs-right-" + index;
  $("." + blobsContainerSelector).append('<div id=' + imgContainerLeft + ' class=gallery-blob-container></div>');
  $("." + blobsContainerSelector).append('<div id=' +imgContainerRight+ ' class="gallery-blob-container di-none"></div>');

  let idx = 0;
  for (var i = 0; i < contentArray.length; i++) {
    $('#' + imgContainerLeft).append('<img src=' + work_url + eval(contentArray[i]) + ' class="gallery-img" draggable=false></img>');
    $('#' + imgContainerRight).append('<img src=' + work_url + eval(contentArray[i]) + ' class="gallery-img" draggable=false></img>');
  }

  var allSrc = getAllSrc(blobsArray);
  $("." + gallerySelector).setGalleryMinHeight(allSrc);

  $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
  $(this).append("<div id=gallery-"+index+"-zoom-container></div>");
  $("#gallery-"+index+"-zoom-container").appendZoom(index, leftItems);
  if (blobsArray.length > 1) $(".left-blobs-gallery-" + index).appendCompare(index, rightItems, imgContainerRight);
}

function getAllImages(repeat, contentArray, work_url) {
  let allSrcEval = [];
  for (var idx = 0; idx < repeat; idx++) {
    var blobs = [];
    for (var j = 0; j < contentArray.length; j++) {
      var img = "<img src=" + work_url + eval(contentArray[j]) + " class=gallery-img draggable=false></img>";
      blobs.push($(img));
    }
    allSrcEval.push(blobs);
  }
  return allSrcEval;
}

function getRepeat(result) {
  var repeatKey = result.repeat.split(".")[0];
  var repeatParam = result.repeat.split(".")[1];
  var repeat;
  if (repeatKey === "params") {
    repeat = eval(result.repeat);
  } else if (repeatKey === "info") {
    repeat = info[repeatParam];
  } else {
    repeat = result.repeat;
  }
  return repeat;
}

function renderRepeatBlobList(galleryIndex, blobListString, gallerySelector, itemSelector, side, repeat, contentArray) {
  $("." + gallerySelector).append("<div class="+ side +"-blobs-gallery-"+ galleryIndex +"></div>");
  $("." + side + "-blobs-gallery-" + galleryIndex).append('<div class="gallery-item-list ' + itemSelector + '"></div>');
  $("." + itemSelector).addMouseOutSelectorEvent(galleryIndex, side, contentArray);
  helpers.addToStorage("gallery-" + galleryIndex + "-" + side, 0);
  for (let idx = 0; idx < repeat; idx++) {
      $("." + itemSelector).append("<span id=gallery-" +galleryIndex+ "-item-" +side+ "-" +idx+ " class=gallery-item-selector>" + eval(blobListString) + "</span>");
      $("#gallery-" +galleryIndex+ "-item-" +side+ "-" +idx).addHoverRepeatFeature(galleryIndex, side, contentArray, idx);
  }
  $("." +itemSelector+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addHoverRepeatFeature = function(galleryIndex, side, contentArray, idx) {
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '#gallery-blobs-' +side+ '-' + galleryIndex;
  $(this).mouseover(function() {
    $(selector).empty();
    var blobs = contentArray[idx];
    for (var i = 0; i < blobs.length; i++) {
      $(selector).append(blobs[i]);
    }
    $("#gallery-" +galleryIndex+ "-zoom > input").updateSize(galleryIndex, side);
    var zoomValue = $("#gallery-" + galleryIndex + "-zoom > input").val();
    helpers.checkInterpolation(zoomValue, selector + " > img");
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    helpers.addToStorage("gallery-" + galleryIndex + "-" + side, idx);
  });
}
  
$.fn.addMouseOutSelectorEvent = function(galleryIndex, side, contentArray) {
  var imgSelector = ".gallery-" + galleryIndex + "-blob-" + side;
  var selector = '#gallery-blobs-' +side+ '-' + galleryIndex;
  $(this).mouseout(function(e) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    var idx = helpers.getFromStorage("gallery-" + galleryIndex + "-" + side);
    $(selector).empty();
    var blobs = contentArray[idx];
    for (var i = 0; i < blobs.length; i++) {
      $(selector).append(blobs[i].clone());
    }
    $("#gallery-" + galleryIndex + "-zoom > input").updateSize(galleryIndex, side);
    var zoomValue = $("#gallery-" +galleryIndex+ "-zoom > input").val();
    helpers.checkInterpolation(zoomValue, selector + " > img");
  });
};