var helpers = clientApp.helpers || {};

$.fn.gallery_new = function(result, index)  {
  if (result.visible) {
    var visible = eval(result.visible);
    if (!visible) return;
  }

  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery_" + index;
  $(this).append("<div class=" + gallerySelector + " ></div>");
  $("." + gallerySelector).addClass("gallery-container");

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  renderGalleryBlobList(index, contentKeys, gallerySelector, result, leftItems, 'left');

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append("<div class=" + blobsContainerSelector + "></div>");
  $("." + blobsContainerSelector).addClass("blobs-wrapper");

  // $("." + gallerySelector).append("<div class=" + rightItems + "></div>");
  renderGalleryBlobList(index, contentKeys, gallerySelector, result, rightItems, 'right');
  $("." + rightItems).addClass("gallery-item-list-right di-none");

  var imgContainerLeft = "gallery-blob-container-left-" + index;
  var imgContainerRight = "gallery-blob-container-right-" + index;
  $("." + blobsContainerSelector).append("<div id=" +imgContainerLeft+ "></div>");
  $("." + blobsContainerSelector).append("<div id=" +imgContainerRight+ "></div>");
  $("#" + imgContainerLeft).addClass("gallery-blob-container");
  $("#" + imgContainerRight).addClass("gallery-blob-container di-none");

  var img = result.contents[contentKeys[0]].img;
  var contentType = typeof(img);
  if (contentType === "string") { // single image
    $("#" + imgContainerLeft).append('<img src=' + work_url + img + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerRight).append('<img src=' + work_url + img + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left di-inline');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right di-inline');
  } else { // array of images
    for (var i = 0; i < img.length; i++) {
      $("#" + imgContainerLeft).append('<img src=' + work_url + img[i] + ' class=gallery-img draggable=false></img>');
      $("#" + imgContainerRight).append('<img src=' + work_url + img[i] + ' class=gallery-img draggable=false></img>');
      $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
    }
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right');
  }
  $("." + leftItems).appendZoom(index, leftItems);
  $("." + leftItems).renderGalleryControlls(index, rightItems, imgContainerRight);
  checkOptions(result.type, index);
}

function renderGalleryBlobList(index, contentKeys, gallerySelector, result, itemSelector, side) {
  $("." + gallerySelector).append("<div class=" + itemSelector + "></div>");
  $("." + itemSelector).addClass("gallery-item-list");
  var contents = result.contents;
  var firstSrc = result.contents[contentKeys[0]].img;
  if (typeof(firstSrc) == "string") {
    firstSrc = [firstSrc];
  }
  for (let i = 0; i < contentKeys.length; i++) {
    if (eval(contents[contentKeys[i]].visible)) {
      $("." + itemSelector).append("<span id=gallery-" +index+ "-item-" +side+ "-" +i+ " class=gallery-item-selector>" + contentKeys[i] + "</span>");
      var content = result.contents[contentKeys[i]].img;
      if (typeof(content) == "string") {
        content = [content];
        firstSrc = result.contents[contentKeys[0]].img;
      }
      $("#gallery-" +index+ "-item-" +side+ "-" +i).addHoverFeature(index, side, firstSrc, work_url, content);
    }
  }
  $("." +itemSelector+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addHoverFeature = function(galleryIndex, side, firstSrc, work_url, src) {
  helpers.addToStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex, firstSrc);
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '#gallery-blob-container-' +side+ '-' + galleryIndex;
  $(this).mouseover(function() {
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      $(selector).append('<img src=' + work_url + src[i] + ' class=gallery-img draggable=false></img>');
      $(selector + " > img").addClass('gallery-' +galleryIndex+ '-blob-'+side);
    }
    $("#gallery-" +galleryIndex+ "-zoom > select").adjustSize(galleryIndex);
  });
  $(this).mouseout(function() {
    $(selector).empty();
    var selectedSrc = helpers.getFromStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex);
    for (var i = 0; i < selectedSrc.length; i++) {
      $(selector).append('<img src=' + work_url + selectedSrc[i] + ' class=gallery-img draggable=false></img>');
      $(selector + " > img").addClass('gallery-' +galleryIndex+ '-blob-'+side);
    }
    $("#gallery-" +galleryIndex+ "-zoom > select").adjustSize(galleryIndex);
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    var selectedSrc = [];
    $(imgSelector).each(function(i){
      let src = $(imgSelector)[i].src.split("/");
      let name = src[src.length - 1];
      selectedSrc.push(name);
    });
    helpers.addToStorage("gallerySelectedSrc-" + side  + "-" + galleryIndex, selectedSrc);
  });
}

$.fn.renderGalleryControlls = function(galleryIndex, rightItems, imgContainerRight) {
  $(this).append("<div><input type=checkbox id=compare-btn-gallery-" +galleryIndex+ "><label for=compare-btn-gallery-" +galleryIndex+ ">Compare</label></div>");
  $("#compare-btn-gallery-" + galleryIndex).on('click', function() {
    if ($(this).is(":checked")) {
      $(".gallery-blobs-container-" + galleryIndex + " > div").css({"flex-basis": "50%"});
    } else {
      $(".gallery-blobs-container-" + galleryIndex + " > div").css({"flex-basis": ""});
    }
    $("#" + imgContainerRight).toggleClass("di-none");
    $(".gallery_" + galleryIndex).toggleClass("space-between");
    $("." + rightItems).toggleClass("di-none");
  });
}

$.fn.updateGalleryWidth = function(galleryIndex) {
  if ($("#compare-btn-gallery-" + galleryIndex).is(":checked")) {
    $(".gallery-blob-container-" + galleryIndex + " > div").toggleClass("flex-50");
  } else {
    $(".gallery-blob-container-" + galleryIndex + " > div").css({"flex-basis": ""});
  }
}

$.fn.appendZoom = function(index, leftItems) {
  var zoom = $("#zoom-container").clone();
  var newZoomID= "gallery-" +index+ "-zoom";
  zoom.attr("id", newZoomID).appendTo("." + leftItems);
  $("#" + newZoomID + " > select").on('change', function() {
    var zoomLevel = $(this).val();
    $("#gallery-blob-container-left-"+index + ", #gallery-blob-container-right-"+index).children('img').each(function(i){
      $(this).height($(this)[0].naturalHeight * zoomLevel);
      $(this).width($(this)[0].naturalWidth * zoomLevel);
    });
  });
  scrollSynq(index);
}

$.fn.adjustSize = function(index) {
  var zoomLevel = $(this).val();
  $("#gallery-blob-container-left-"+index + ", #gallery-blob-container-right-"+index).children('img').each(function(i){
    $(this).height($(this)[0].naturalHeight * zoomLevel);
    $(this).width($(this)[0].naturalWidth * zoomLevel);
  });
}

function scrollSynq(index) {
  var isSyncingLeftScroll = false;
  var isSyncingRightScroll = false;
  var leftDiv = document.getElementById('gallery-blob-container-left-' + index);
  var rightDiv = document.getElementById('gallery-blob-container-right-' + index);
  $('#gallery-blob-container-left-' + index).attachDragger();
  $('#gallery-blob-container-right-' + index).attachDragger();

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
