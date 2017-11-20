var helpers = clientApp.helpers || {};

$.fn.video_gallery = function (result, index) {
  if (result.visible) {
    var visible = eval(result.visible);
    if (!visible) return;
  }

  var contentKeys = Object.keys(result.contents);

  if (result.label) $(this).appendLabel(result.label);
  var gallerySelector = 'gallery-' + index;
  $(this).append('<div class="' + gallerySelector + ' gallery-container" ></div>');
  $(this).appendVideoTools();

  var blobsArray = getGalleryVideos(result.contents, work_url);

  var leftItems = 'left-blobs-' + index;
  var rightItems = 'right-blobs-' + index;
  renderVideoGalleryBlobList(index, contentKeys, result, leftItems, 'left', blobsArray);

  var blobsContainerSelector = 'gallery-' + index + '-blobs-container';
  $('.' + gallerySelector).append('<div id="' + blobsContainerSelector + '" class="blobs-wrapper"></div>');

  renderVideoGalleryBlobList(index, contentKeys, result, rightItems, 'right', blobsArray);
  $('.' + rightItems).addClass('gallery-item-list-right di-none');

  var videoContainerLeft = 'video-container-left-' + index;
  var videoContainerRight = 'video-container-right-' + index;
  $('#' + blobsContainerSelector).append('<div id="' + videoContainerLeft + '" class=gallery-video-container></div>');
  $('#' + blobsContainerSelector).append('<div id="' + videoContainerRight + '" class="gallery-video-container di-none"></div>');

  for (let i = 0; i < blobsArray.length; i++) {
    $('#' + videoContainerLeft).append('<div></div>');
    $('#' + videoContainerRight).append('<div></div>');
    for (let j = 0; j < blobsArray[i].length; j++) {
      var leftClone = blobsArray[i][j].clone();
      var rightClone = blobsArray[i][j].clone();
      $('#' + videoContainerLeft + ' > div:nth-child(' + (i+1) + ')').append($(leftClone));
      $('#' + videoContainerRight + ' > div:nth-child(' + (i+1) + ')').append($(rightClone));
    }
  }
  $('#' + videoContainerLeft).initVideoProps();
  $('#' + videoContainerRight).initVideoProps();

  var allSrc = getAllSrc(blobsArray);
  $('.' + gallerySelector).setVideoGalleryMinHeight(allSrc);
  if (blobsArray.length > 1) $('.' + leftItems).appendVideoCompare(index, rightItems, videoContainerRight);
}

$.fn.initVideoProps = function () {
  $(' div:first-child > video', this).on('loadedmetadata', function() {
    $(this).prop('muted', false);
  });
  $(' > div:not(:first-child)', this).addClass('di-none');
}

// Set gallery min-height to avoid jump loops.
$.fn.setVideoGalleryMinHeight = function (sources) {
  var minHeight;
  var selector = $(this);
  if (!Array.isArray(sources)) {
    sources = Object.keys(sources).map(function (e) {
      return sources[e];
    });
  }
  for (let i = 0; i < sources.length; i++) {
    let tmpVideo = document.createElement('video');
    tmpVideo.src = sources[i];
    $(tmpVideo).on("loadedmetadata", function () {
      minHeight = parseInt(selector.css('min-height'));
      var videoHeight = $(this)[0].videoHeight;
      if (minHeight < videoHeight) {
        minHeight = videoHeight < 580 ? videoHeight : 580;
        selector.css({ minHeight: minHeight + 20 + 'px' });
      }
    });
  }
};

function getGalleryVideos(contentArray, work_url) {
  var allSrc = [];
  var keys = Object.keys(contentArray);
  for (var i = 0; i < keys.length; i++) {
    var blobSetContent = contentArray[keys[i]];
    var visibleField = blobSetContent.hasOwnProperty('visible');
    if (!visibleField || (visibleField && eval(blobSetContent.visible))) {
      var videoField = blobSetContent.video;
      var repeat = blobSetContent.repeat !== undefined ? checkRepeat(blobSetContent.repeat) : 1;
      var blobs = [];
      for (var idx = 0; idx < repeat; idx++) {
        blobs = [];
        if (typeof (videoField) === 'string') {
          var video = '<video src=' + work_url + (videoField.indexOf("'") == -1 ? videoField : eval(videoField)) + ' class=gallery-video draggable=false controls muted></video>';
          blobs.push($(video));
        } else if (typeof (videoField) === 'object') {
          for (var k = 0; k < videoField.length; k++) {
            var video = '<video src=' + work_url + (videoField[k].indexOf("'") == -1 ? videoField[k] : eval(videoField[k])) + ' class=gallery-video draggable=false controls muted></video>';
            blobs.push($(video));
          }
        }
        allSrc.push(blobs);
      }
    }
  }
  return allSrc;
}

function renderVideoGalleryBlobList(index, contentKeys, result, itemSelector, side, blobsArray) {
  $('.gallery-' + index).append('<div class="' + itemSelector + ' gallery-item-list"></div>');
  $('.' + itemSelector).append('<div id=gallery-' + index + '-blobList-' + side + ' class=gallery-blobList-left></div>');
  var contents = result.contents;
  var firstVisibleBlob = true;
  var itemIndex = 0;
  for (let i = 0; i < contentKeys.length; i++) {
    var visibleField = contents[contentKeys[i]].hasOwnProperty('visible');
    if (!visibleField || (visibleField && eval(contents[contentKeys[i]].visible))) {
      if (firstVisibleBlob) {
        helpers.addToStorage('gallery-' + index + '-' + side, itemIndex);
        firstVisibleBlob = false;
      }
      var line = contents[contentKeys[i]];
      var repeat = line.repeat != undefined ? checkRepeat(line.repeat) : 1;
      for (var idx = 0; idx < repeat; idx++) {
        var text = getEvalText(contentKeys[i]);
        var spanId = 'gallery-' + index + '-item-' + side + '-' + i + '-' + idx;
        $('#gallery-' + index + '-blobList-' + side).append('<span id=' + spanId + ' class=gallery-item-selector>' + eval(text) + '</span>');
        $('#' + spanId).videoHover(index, side, itemIndex);
        itemIndex++;
      }
    }
  }
  $('#gallery-' + index + '-blobList-' + side).mouseOutVideo(index, side, blobsArray);
  $('.' + itemSelector + ' span:first-child').addClass('gallery-item-selected');
}

$.fn.videoHover = function (galleryIndex, side, id) {
  var videoSelector = '.gallery-' + galleryIndex + '-blob-' + side;
  var selector = '#video-container-' + side + '-' + galleryIndex;
  $(this).mouseover(function () {
    $(selector + ' > div').addClass('di-none');
    $(selector + ' video').prop('muted', true);
    $(selector + ' > div:nth-child(' + (id+1) + ')').removeClass('di-none');
    $(selector + ' > div:nth-child(' + (id + 1) + ') > video').prop('muted', false);
  });
  $(this).on('click', function () {
    $('#gallery-' + galleryIndex + '-blobList-' + side + ' > .gallery-item-selected').toggleClass('gallery-item-selected');
    $(this).toggleClass('gallery-item-selected');
    helpers.addToStorage('gallery-' + galleryIndex + '-' + side, id);
  });
}

$.fn.mouseOutVideo = function (galleryIndex, side, blobsArray) {
  var selector = '#video-container-' + side + '-' + galleryIndex;
  $(this).mouseout(function (event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    var selectedSrc = helpers.getFromStorage('gallery-' + galleryIndex + '-' + side);
    $(selector + ' > div').addClass('di-none');
    $(selector + ' video').prop('volume', 0);
    $(selector + ' > div:nth-child(' + (selectedSrc + 1) + ')').removeClass('di-none');
    $(selector + ' > div:nth-child(' + (selectedSrc + 1) + ') video').prop('volume', 1);
  });
}

$.fn.appendVideoCompare = function (galleryIndex, rightItems, videoContainerRight) {
  $(this).append('<div class=p-y-10><input type=checkbox id=compare-btn-gallery-' + galleryIndex + '><label for=compare-btn-gallery-' + galleryIndex + '>Compare</label></div>');
  $('#compare-btn-gallery-' + galleryIndex).on('click', function () {
    if ($(this).is(':checked')) {
      $('#video-container-left-' + galleryIndex).css({ 'flex-basis': '50%' });
      $('#video-container-right-' + galleryIndex).css({ 'flex-basis': '50%' });
      $('#gallery-' + galleryIndex + '-blobs-container').addClass('blobs-wrapper-compare');
    } else {
      $('#video-container-left-' + galleryIndex).css({ 'flex-basis': "" });
      $('#video-container-right-' + galleryIndex).css({ 'flex-basis': "" });
      $('#gallery-' + galleryIndex + '-blobs-container').removeClass('blobs-wrapper-compare');
    }
    $('#' + videoContainerRight).toggleClass('di-none');
    $('.gallery-' + galleryIndex).toggleClass('space-between');
    $('.' + rightItems).toggleClass('di-none');
  });
}
  

$.fn.appendVideoTools = function() {
  $('<div class=video-tools ></div>')
  .appendTo($(this))
  .append('<span class="play-pause-btn pause-to-play" ></span>')
  .append('<span class=stop-btn ></span>');
  
  var videoGallery = $(this);
  var playPauseBtn = $('.play-pause-btn', this);
  
  $('.play-pause-btn', this).click(function () {
    if($(this).hasClass('pause-to-play')) $('video', videoGallery).playVideos();
    else if ($(this).hasClass('play-to-pause')) $('video', videoGallery).pauseVideos();
    
    $(this).toggleClass('play-to-pause pause-to-play');
  });
  
  $('.stop-btn', this).click(function() {
    $('video', videoGallery).stopVideos();
    playPauseBtn.attr('class', 'play-pause-btn pause-to-play');
  });
}

$.fn.playVideos = function() {
  $(this).each(function() {
    $(this)[0].play();
  });
} 

$.fn.pauseVideos = function() {
  $(this).each(function () {
    $(this)[0].pause();
  });
}

$.fn.stopVideos = function() {
  $(this).each(function () {
    $(this)[0].pause();
    $(this)[0].currentTime = 0;
  });
}
