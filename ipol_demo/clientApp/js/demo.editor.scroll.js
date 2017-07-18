var scrollController = scrollController || {};

// Drag editor image mouse events
$.fn.attachDragger = function() {
  var attachment = false,
    lastPosition, position, difference;
  $(this).on("mousedown mouseup mousemove", function(e) {
    if (e.type == "mousedown") attachment = true, lastPosition = [e.clientX, e.clientY];
    if (e.type == "mouseup") attachment = false;
    if (e.type == "mousemove" && attachment == true) {
      position = [e.clientX, e.clientY];
      difference = [(position[0] - lastPosition[0]), (position[1] - lastPosition[1])];
      $(this).scrollLeft($(this).scrollLeft() - difference[0]);
      $(this).scrollTop($(this).scrollTop() - difference[1]);
      lastPosition = [e.clientX, e.clientY];
    }
  });
  $(window).on("mouseup", function() {
    attachment = false;
  });
};

scrollController.addScrollingEvents = function() {
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
