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
  var idx = 0;
  if (contentType === "string") { // single image
    $("#" + imgContainerLeft).append('<img src=' + work_url + (img.indexOf("'") == -1 ? img : eval(img)) + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerRight).append('<img src=' + work_url + (img.indexOf("'") == -1 ? img : eval(img)) + ' class=gallery-img draggable=false></img>');
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left di-inline');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right di-inline');
  } else { // array of images
    for (var i = 0; i < img.length; i++) {
      $("#" + imgContainerLeft).append('<img src=' + work_url + (img[i].indexOf("'") == -1 ? img[i] : eval(img[i])) + ' class=gallery-img draggable=false></img>');
      $("#" + imgContainerRight).append('<img src=' + work_url + (img[i].indexOf("'") == -1 ? img[i] : eval(img[i])) + ' class=gallery-img draggable=false></img>');
    }
    $("#" + imgContainerLeft + " > img").addClass('gallery-' +index+ '-blob-left');
    $("#" + imgContainerRight + " > img").addClass('gallery-' +index+ '-blob-right');
  }
  $("#" + imgContainerLeft + ", #" + imgContainerRight).addClass("di-flex");
  $(this).append("<div id=gallery-" + index + "-zoom-container></div>");
  $("#gallery-" + index + "-zoom-container").appendZoom(index, leftItems);
  $("." + leftItems).renderGalleryControlls(index, rightItems, imgContainerRight);
  checkOptions(result.type, index);
}

function checkRepeat(line, repeatKey, repeatParam) {
  if (repeatKey === "params") {
    var repeatValues = JSON.stringify(params);
    var repeat = repeatValues[repeatParam];
  } else if (repeatKey === "info") {
    var repeat = info[repeatParam];
  } else {
    repeat = eval(line.repeat);
  }
  return repeat;
}

function renderGalleryBlobList(index, contentKeys, gallerySelector, result, itemSelector, side) {
  $("." + gallerySelector).append("<div class=" + itemSelector + "></div>");
  $("." + itemSelector).addClass("gallery-item-list");
  var contents = result.contents;
  var firstSrc = result.contents[contentKeys[0]].img;
  var firstVisibleBlob = true;
  if (typeof(firstSrc) == "string") {
    firstSrc = [firstSrc];
  }
  for (let i = 0; i < contentKeys.length; i++) {
    if (eval(contents[contentKeys[i]].visible)) {
      var content = result.contents[contentKeys[i]].img;
      if (typeof(content) == "string") {
        content = [content];
        firstSrc = content;
      }
      var srcStorage = [];
      for (let k = 0; k < firstSrc.length; k++) {
        var idx = k;
        srcStorage[k] = work_url + (firstSrc[k].indexOf("'") == -1 ? firstSrc[k] : eval(firstSrc[k]));
      }
      if (firstVisibleBlob) {
        console.log(srcStorage);
        helpers.addToStorage("gallery-" + index + "-" + side, srcStorage);
        firstVisibleBlob = false;
      }
      var line = contents[contentKeys[i]];
      var spanContainer = "<div id=gallery-"+index+"-blobList-"+side+" class=gallery-blobList-left></div>";
      $("." + itemSelector).append(spanContainer);
      if (line.repeat) {
        line.repeat = line.repeat.toString();
        var repeatSplit = line.repeat.split(".");
        var repeat = checkRepeat(line, repeatSplit[0], repeatSplit[1]);
        for (var idx = 0; idx < repeat; idx++) {
          var text = getEvalText(contentKeys[i]);
          $("#gallery-"+index+"-blobList-"+side).append("<span id=gallery-" +index+ "-item-" +side+ "-" + i +idx+ " class=gallery-item-selector>" + eval(text) + "</span>");
          var evalContents = [];
          for (var j = 0; j < content.length; j++) {
            evalContents[j] = work_url + (content[j].indexOf("'") == -1 ? content[j] : eval(content[j]));
          }
          $("#gallery-" +index+ "-item-" +side+ "-" + i +idx).addHoverFeature(index, side, work_url, evalContents, idx);
        }
      } else {
        var text = getEvalText(contentKeys[i]);        
        $("#gallery-"+index+"-blobList-"+side).append("<span id=gallery-" +index+ "-item-" +side+ "-" +i+ " class=gallery-item-selector>" + eval(text) + "</span>");
        var evalContents = [];
        for (var j = 0; j < content.length; j++) {
          evalContents[j] = work_url + (content[j].indexOf("'") == -1 ? content[j] : eval(content[j]));
        }
        $("#gallery-" +index+ "-item-" +side+ "-" +i).addHoverFeature(index, side, work_url, evalContents, 0);
      }
    }
  }
  $(this).addMouseOut(index, side);
  $("." +itemSelector+ " span:first-child").addClass("gallery-item-selected");
}

$.fn.addMouseOut = function (galleryIndex, side) {
  var selector = '#gallery-blob-container-' + side + '-' + galleryIndex;
  $("#gallery-" + galleryIndex + "-blobList-" + side).mouseout(function (event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    console.log("OUT");
    var selectedSrc = helpers.getFromStorage("gallery-" + galleryIndex + "-" + side);
    $(selector).empty();
    console.log(selectedSrc);
    for (var i = 0; i < selectedSrc.length; i++) {
      var elem = '<img src=' + (selectedSrc[i].indexOf("'") == -1 ? selectedSrc[i] : eval(selectedSrc[i])) + ' class=gallery-img draggable=false></img>';
      $(elem).appendTo(selector);
      $(elem).on('load', function () {
        $("#gallery-" + galleryIndex + "-zoom > input").adjustSize(galleryIndex);
      });
      $(selector + " > img").addClass('gallery-' + galleryIndex + '-blob-' + side);
    }
    $("#gallery-" + galleryIndex + "-zoom > input").adjustSize(galleryIndex);
  });
}

function getEvalText(str) {
  if (str.indexOf('+') != -1) {
    return str;
  } else {
    return "\'"+str+"\'";
  }
}

$.fn.addHoverFeature = function(galleryIndex, side, work_url, src, idx) {
  var imgSelector = '.gallery-' +galleryIndex+ '-blob-' + side;
  var selector = '#gallery-blob-container-' +side+ '-' + galleryIndex;
  $(this).mouseover(function() {
    $(selector).empty();
    for (var i = 0; i < src.length; i++) {
      var elem = '<img src=' + (src[i].indexOf("'") == -1 ? src[i] : eval(src[i])) + ' class=gallery-img draggable=false></img>';
      $(elem).appendTo(selector);
      $(elem).on('load', function () {
        $("#gallery-" + galleryIndex + "-zoom > input").adjustSize(galleryIndex);
      });
      $(selector + " > img").addClass('gallery-' +galleryIndex+ '-blob-'+side);
    }
    $("#gallery-" +galleryIndex+ "-zoom > input").adjustSize(galleryIndex);
  });
  $(this).on('click', function() {
    var listSelector = ".gallery-" +side+ "-items-" + galleryIndex;
    $("#gallery-" + galleryIndex + "-blobList-" + side + " > .gallery-item-selected").toggleClass("gallery-item-selected");
    $(this).toggleClass("gallery-item-selected");
    var selectedSrc = [];
    $(imgSelector).each(function(i){
      selectedSrc.push($(imgSelector)[i].src);
    });
    helpers.addToStorage("gallery-" +galleryIndex + "-" + side, selectedSrc);
  });
}

$.fn.renderGalleryControlls = function(galleryIndex, rightItems, imgContainerRight) {
  $(this).append("<div class=p-y-10><input type=checkbox id=compare-btn-gallery-" +galleryIndex+ "><label for=compare-btn-gallery-" +galleryIndex+ ">Compare</label></div>");
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

$.fn.appendZoom = function(index, leftItems) {
  var zoom = $("#zoom-container").clone();
  var newZoomID= "gallery-" +index+ "-zoom";
  zoom.attr("id", newZoomID).appendTo($(this));
  zoom.removeClass("di-none");
  $("#" + newZoomID + " > input").on('input', function() {
    var zoomLevel = $(this).val();
    $(this).adjustSize(index);
    $("#gallery-" + index + "-zoom > span").html(zoomLevel + "x");
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