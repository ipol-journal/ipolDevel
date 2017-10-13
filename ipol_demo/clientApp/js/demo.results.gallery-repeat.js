var helpers = clientApp.helpers || {};

$.fn.repeat_gallery = function(result, index)  {
  if (result.visible) {
    var visible = eval(result.visible);
    if (!visible) return;
  }

  var blobListString = result.contents[0];
  var contentArray = result.contents[1];
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
  if (typeof(contentArray) == "string") {
    contentArray = [contentArray]
  } else if (typeof(contentArray) == "object") {
    let titles = Object.keys(contentArray);
    contentArray = Object.keys(contentArray).map(function(e) {
      return contentArray[e];
    });
  }
  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery_" + index;
  $(this).append("<div class=" + gallerySelector + " ></div>");
  $("." + gallerySelector).addClass("gallery-container");

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  renderRepeatBlobList(index, blobListString, gallerySelector, leftItems, 'left', repeat, contentArray);

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append("<div class=" + blobsContainerSelector + "></div>");
  $("." + blobsContainerSelector).addClass("blobs-wrapper");
  renderRepeatBlobList(index, blobListString, gallerySelector, rightItems, 'right', repeat, contentArray);
  $("." + rightItems).addClass("gallery-item-list-right di-none");

  // Append both sides image containers
  var imgContainerLeft = "gallery-blob-container-left-" + index;
  var imgContainerRight = "gallery-blob-container-right-" + index;
  $("." + blobsContainerSelector).append("<div id=" +imgContainerLeft+ "></div>");
  $("." + blobsContainerSelector).append("<div id=" +imgContainerRight+ "></div>");
  $("#" + imgContainerLeft).addClass("gallery-blob-container");
  $("#" + imgContainerRight).addClass("gallery-blob-container di-none");

  let idx = 0;
  var src = [];
  for (var i = 0; i < contentArray.length; i++) {
    $("#" + imgContainerLeft).append('<img src=' + work_url + eval(contentArray[i]) + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerRight).append('<img src=' + work_url + eval(contentArray[i]) + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerLeft).append('<p id=gallery-' +index+ '-blob-title-Left></p>');
    $("#" + imgContainerRight).append('<p id=gallery-' +index+ '-blob-title-Right></p>');
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left di-inline');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right di-inline');
    src.push(eval(contentArray[i]));
  }
  $("." + gallerySelector).setGalleryMinHeight(work_url, src);

  $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
  $(this).append("<div id=gallery-"+index+"-zoom-container></div>");
  $("#gallery-"+index+"-zoom-container").appendZoom(index, leftItems);
  if ($(".gallery-left-items-" +index + " > span").length > 1) $("." + leftItems).renderGalleryControls(index, rightItems, imgContainerRight);
  checkOptions(result.type, index);
}

function renderRepeatBlobList(galleryIndex, blobListString, gallerySelector, itemSelector, side, repeat, contentArray) {
  $("." + gallerySelector).append("<div class=" + itemSelector + "></div>");
  $("." + itemSelector).addClass("gallery-item-list");
  for (let idx = 0; idx < repeat; idx++) {
    // if (eval(contents[contentArray[i]].visible)) {
      $("." + itemSelector).append("<span id=gallery-" +galleryIndex+ "-item-" +side+ "-" +idx+ " class=gallery-item-selector>" + eval(blobListString) + "</span>");
      $("#gallery-" +galleryIndex+ "-item-" +side+ "-" +idx).addHoverRepeatFeature(galleryIndex, side, work_url, contentArray, idx);
    // }
  }
  $("." +itemSelector+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addHoverRepeatFeature = function(galleryIndex, side, work_url, contentArray, idx) {
  helpers.addToStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex, 0);
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '.gallery-blob-container-' +side+ '-' + galleryIndex;
  $(this).mouseover(function() {
    $(selector).addClass("flex-50");
    $(imgSelector).each(function(i) {
      $(this).attr("src", work_url + eval(contentArray[i]));
      $("#gallery-" +galleryIndex+ "-zoom > input").updateSize(galleryIndex);
    });
  });
  $(this).mouseout(function() {
    var idx = helpers.getFromStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex);
    $(imgSelector).each(function(i){
      $(this).attr("src", work_url + eval(contentArray[i]));
      $("#gallery-" +galleryIndex+ "-zoom > input").updateSize(galleryIndex);
    });
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    helpers.addToStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex, idx);
  });
}
