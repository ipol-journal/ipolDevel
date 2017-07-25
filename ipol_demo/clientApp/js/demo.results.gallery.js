$.fn.gallery_new = function(result, index)  {
  var visible = eval(result.visible);
  if (!visible) return;

  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = "gallery_" + index;
  $(this).append("<div class=" + gallerySelector + " ></div>");
  $("." + gallerySelector).addClass("gallery-container");

  var leftItems = "gallery-left-items-" + index;
  var rightItems = "gallery-right-items-" + index;
  renderGalleryBlobLists(index, contentKeys, gallerySelector, result, leftItems, rightItems);

  var blobsContainerSelector = "gallery-blobs-container-" + index;
  $("." + gallerySelector).append("<div class=" + blobsContainerSelector + "></div>");
  $("." + blobsContainerSelector).addClass("blobs-wrapper");

  $("." + gallerySelector).append("<div class=" + rightItems + "></div>");
  $("." + rightItems).addClass("gallery-item-list di-none");

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
  $("." + leftItems).appendGalleryControlls(index, rightItems, imgContainerRight);
  checkOptions(result.type, index);
}

function renderGalleryBlobLists(index, contentKeys, gallerySelector, result, leftItems, rightItems) {
  $("." + gallerySelector).append("<div class=" + leftItems + "></div>");
  $("." + leftItems).addClass("gallery-item-list");
  var contents = result.contents;
  for (let i = 0; i < contentKeys.length; i++) {
    if (eval(contents[contentKeys[i]].visible)) {
      $("." + leftItems).append("<span id=gallery-" +index+ "-item-left-" +i+ " class=gallery-item-selector>" + contentKeys[i] + "</span>");
      $("." + rightItems).append("<span id=gallery-" +index+ "-item-right-" +i+ " class=gallery-item-selector>" + contentKeys[i] + "</span>");
      var content = result.contents[contentKeys[i]].img;
      if (typeof(content) == "string") content = [content];
      $("#gallery-" +index+ "-item-left-" +i).addHoverFeature(index, 'left', work_url, content);
      $("#gallery-" +index+ "-item-right-" +i).addHoverFeature(index, 'right', work_url, content);
    }
  }
  $("." +leftItems+ " span:first-child").addClass("gallery-item-selected");
  $("." +rightItems+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addHoverFeature = function(galleryIndex, side, work_url, src) {
  var originalSrc = "";
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '#gallery-blob-container-' +side+ '-' + galleryIndex;
  var originalSrc = [];
  $(this).mouseover(function() {
    $(imgSelector).each(function(i) {
      originalSrc.push($(imgSelector)[i].src);
    });
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      $(selector).append('<img src=' + work_url + src[i] + ' class=gallery-img draggable=false></img>');
    }
    $("#gallery-" +galleryIndex+ "-zoom > select").updateSize(galleryIndex);
  });
  $(this).mouseout(function() {
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      $(selector).append('<img src=' + work_url + src[i] + ' class=gallery-img draggable=false></img>');
    }
    $("#gallery-" +galleryIndex+ "-zoom > select").updateSize(galleryIndex);
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $(listSelector + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    originalSrc = [];
    $(imgSelector).each(function(i){
      originalSrc.push($(imgSelector)[i].srcsrc);
    });
  });
}
