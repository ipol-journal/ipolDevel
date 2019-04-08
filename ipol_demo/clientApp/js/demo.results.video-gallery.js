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
  
  var blobsArray = getGalleryVideos(result.contents, work_url);
  
  var leftItems = 'left-blobs-' + index;
  var rightItems = 'right-blobs-' + index;
  renderVideoGalleryBlobList(index, contentKeys, result, leftItems, 'left', blobsArray);
  
  var blobsContainerSelector = 'gallery-' + index + '-blobs-container';
  $('.' + gallerySelector).append('<div id="' + blobsContainerSelector + '" class="blobs-wrapper"></div>');
  
  renderVideoGalleryBlobList(index, contentKeys, result, rightItems, 'right', blobsArray);
  $('.' + rightItems).addClass('gallery-item-list-right di-none');
  
  var videoContainerLeft = 'gallery-blobs-left-' + index;
  var videoContainerRight = 'gallery-blobs-right-' + index;
  $('#' + blobsContainerSelector).append('<div id="' + videoContainerLeft + '" class=gallery-video-container></div>');
  $('#' + blobsContainerSelector).append('<div id="' + videoContainerRight + '" class="gallery-video-container di-none"></div>');
  
  for (let i = 0; i < blobsArray.length; i++) {
    $('#' + videoContainerLeft).append('<div></div>');
    $('#' + videoContainerRight).append('<div></div>');
    for (let j = 0; j < blobsArray[i].length; j++) {
      var leftClone = blobsArray[i][j].clone();
      var rightClone = blobsArray[i][j].clone();
      leftClone.addFinishedEvent();
      rightClone.addFinishedEvent();
      $('#' + videoContainerLeft + ' > div:nth-child(' + (i+1) + ')').append($(leftClone));
      $('#' + videoContainerRight + ' > div:nth-child(' + (i+1) + ')').append($(rightClone));
    }
  }
  $('#' + videoContainerLeft).initVideoProps();
  $('#' + videoContainerRight).initVideoProps();
  $('#' + videoContainerRight + ' div:first-child > video').on('loadedmetadata', function () {
    $(this).prop('muted', true);
  });
  
  var allSrc = getAllSrc(blobsArray);
  $('.' + gallerySelector).setVideoGalleryMinHeight(allSrc);
  if (blobsArray.length > 1) $('.' + leftItems).appendVideoCompare(index, rightItems, videoContainerRight);
  scrollSync(index);
  $(this).appendVideoTools();
}

$.fn.addFinishedEvent = function () {
  $(this)[0].onended = function () {
    let galleryVideos = $(this).parents().eq(2).find($('video'));
    let playPauseBtn = $(this).parents().eq(4).find($('div.video-tools .play-pause-btn'));
    for(let video of galleryVideos)
      if(!video.paused || !video.ended) return;
    playPauseBtn.attr('status', "paused")
    playPauseBtn.removeClass('pause-btn');
    playPauseBtn.attr("src", "assets/media-controls/play.svg");
  }
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
  var selector = '#gallery-blobs-' + side + '-' + galleryIndex;
  $(this).mouseover(function () {
    $(selector + ' > div').addClass('di-none');
    $(selector + ' video').each(function() {
      $(this).prop('muted', true);
    });
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
  var selector = '#gallery-blobs-' + side + '-' + galleryIndex;
  $(this).mouseout(function (event) {
    e = event.toElement || event.relatedTarget;
    if (e != null && (e.parentNode == this || e == this)) {
      return;
    }
    var selectedSrc = helpers.getFromStorage('gallery-' + galleryIndex + '-' + side);
    $(selector + ' > div').addClass('di-none');
    $(selector + ' video').prop('muted', true);
    $(selector + ' > div:nth-child(' + (selectedSrc + 1) + ')').removeClass('di-none');
    $(selector + ' > div:nth-child(' + (selectedSrc + 1) + ') video').prop('muted', false);
  });
}

$.fn.appendVideoCompare = function (galleryIndex, rightItems, videoContainerRight) {
  $(this).append('<div class=p-y-10><input type=checkbox id=compare-btn-gallery-' + galleryIndex + '><label for=compare-btn-gallery-' + galleryIndex + '>Compare</label></div>');
  $('#compare-btn-gallery-' + galleryIndex).on('click', function () {
    if ($(this).is(':checked')) {
      $('#gallery-blobs-left-' + galleryIndex).css({ 'flex-basis': '50%' });
      $('#gallery-blobs-right-' + galleryIndex).css({ 'flex-basis': '50%' });
      $('#gallery-' + galleryIndex + '-blobs-container').addClass('blobs-wrapper-compare');
    } else {
      $('#gallery-blobs-left-' + galleryIndex).css({ 'flex-basis': "" });
      $('#gallery-blobs-right-' + galleryIndex).css({ 'flex-basis': "" });
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
    .append('<div class=play-stop-container ><img class=play-pause-btn status=paused src=assets/media-controls/play.svg alt=play-pause>\
                  <img class=stop-btn src=assets/media-controls/stop.svg alt=stop></div>')
  .append('<div><img class=skip-backwards-1 src=assets/media-controls/step-backwards-1.svg alt=step-backwards-1s></div>')
  .append('<div><img class=skip-forward-1 src=assets/media-controls/step-forward-1.svg alt=step-forward-1s></div>')
  .append('<div><img class=skip-backwards-5 src=assets/media-controls/step-backwards-5.svg alt=step-backwards-5s></div>')
  .append('<div><img class=skip-forward-5 src=assets/media-controls/step-forward-5.svg alt=step-forward-5s></div>')
  .append('<div class=speed_control><img class=decrease_speed src=assets/media-controls/decrease.svg alt=decrease_speed><span class=speed><span class=speed_num>1.00</span>x</span><img class=increase_speed src=assets/media-controls/increase.svg alt=increase_speed></div>')
  .append('<div><img class=loop src=assets/media-controls/loop.svg alt=loop status=off></div>')
  $('.video-tools').css('margin-left', $('#gallery-0-blobs-container')[0].offsetLeft + 5)
  
  var videoGallery = $(this);
  
  $('.play-pause-btn', this).click(function () {
    if($(this).attr('status') == "paused"){
      $('video', videoGallery).playVideos();
      $(this).attr('status', "playing")
      $(this).addClass('pause-btn');
      $(this).attr("src", "assets/media-controls/pause.svg");
    } else {
      $('video', videoGallery).pauseVideos();
      $('video', videoGallery).syncVideos($('video', videoGallery)[0].currentTime);
      $(this).attr('status', "paused")
      $(this).removeClass('pause-btn');
      $(this).attr("src", "assets/media-controls/play.svg");
    } 
  });
  
  $('.stop-btn', this).click(function() {
    $('video', videoGallery).stopVideos();
    $(".play-pause-btn").attr('status', "paused")
    $(".play-pause-btn").removeClass('pause-btn');
    $(".play-pause-btn").attr("src", "assets/media-controls/play.svg");
  });

  $('.decrease_speed', this). click(function(){
    $('video', videoGallery).decreasePlaybackRate();
    $(".speed_num", videoGallery)[0].textContent = ($("video", videoGallery)[0].playbackRate).toFixed(2);
  });

  $('.increase_speed', this). click(function(){
    $('video', videoGallery).increasePlaybackRate();
    $(".speed_num", videoGallery)[0].textContent = ($("video", videoGallery)[0].playbackRate).toFixed(2);
  });

  $('.skip-forward-1', this).click(function(){
    $('video', videoGallery).skipForward(1);
  })

  $('.skip-backwards-1', this).click(function(){
    $('video', videoGallery).skipBackwards(1);
  })

  $('.skip-forward-5', this).click(function(){
    $('video', videoGallery).skipForward(5);
  })

  $('.skip-backwards-5', this).click(function(){
    $('video', videoGallery).skipBackwards(5);
  })

  $('.loop', this).click(function () {
    if ($(this).attr("status") == "off") $(this).attr("status", "on")
    else $(this).attr("status", "off")
    
    $('video', videoGallery).loop();
  })
}

$.fn.skipForward = function(time){
  $(this).each(function () {
    $(this)[0].currentTime += time;
  });
}


$.fn.skipBackwards = function(time){
  $(this).each(function () {
    $(this)[0].currentTime -= time;
  });
}

$.fn.loop = function () {
  $(this).each(function () {
    $(this)[0].loop = !$(this)[0].loop;
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

$.fn.decreasePlaybackRate = function(){
  speeds = [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
  current_speed = $(this)[0].playbackRate;
  if(current_speed == 0.1) return;
  
  $(this).each(function () {
    $(this)[0].playbackRate = speeds[speeds.indexOf(current_speed) - 1];
  });
}

$.fn.increasePlaybackRate = function () {
  speeds = [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
  current_speed = $(this)[0].playbackRate;
  if (current_speed == 2) return;

  $(this).each(function () {
    $(this)[0].playbackRate = speeds[speeds.indexOf(current_speed) + 1];
  });
}

$.fn.resetPlaybackRate = function() {
  $(this).each(function () {
    $(this)[0].playbackRate = 1.0;
  });
}

$.fn.syncVideos = function(time){ 
  $(this).each(function () {
    $(this)[0].currentTime = time;
  });
}