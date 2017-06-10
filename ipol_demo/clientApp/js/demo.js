"use strict"

var demo_id;

// Initial trigger.
$(document).ready(function() {
  $("#header").load("header.html");
  $("#inputEditorContainer").load("editor.html");
  $("#parameters").load("parameters.html");
  $("#footer").load("footer.html");
  var clientApp = (function() {
    var demoInfo;

    var printInputSection = function() {
      input.printInput();
    };

    return {
      printInputSection: printInputSection
    };
  })();
  clearStorage();
  demo_id = getDemoId();
  clientApp.printInputSection();
});

// Get Demo_Id from URL.
function getDemoId() {
  var urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('id');
}

// Clear all sessionStorage.
function clearStorage() {
  Object.keys(sessionStorage).forEach(function(key) {
    sessionStorage.removeItem(key);
  });
}

$(function() {
  $(document).tooltip({
    content: function() {
      return $(this).prop('title');
    }
  });
});
