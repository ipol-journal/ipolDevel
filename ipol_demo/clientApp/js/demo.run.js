var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};

var errorMsg = "Error.";
var runData = {};

$(".run-btn").click(function() {
  runDemo();
});

function runDemo() {
  runData = {};
  setRunPostData();

  // si no lo tiene 30. si lo tiene lo que especifique.
  $.ajax({
      url: '/api/core/run2',
      type: 'POST',
      dataType: 'json',
      beforeSend: function() {
        hideRunningAnimation();
        hideStatusContainer();
        displayRunningAnimation();
        return checkPostData();
      },
      data: runData
    })
    .done(function(res) {
      console.log(res);
      if (res.status == "KO") displayError(res.error);
      else displaySuccess("Excecution successful");
      //Call drawResults function
    })
    .fail(function(res) {
      console.log(res);
      displayError(res.responseText);
    })
    .always(function(res) {
      hideRunningAnimation();
      enableRunButton();
    });
}

function setRunPostData() {
  var origin = helpers.getFromStorage("origin");
  runData.demo_id = demo_id;
  runData.params = params;
  if (origin) runData.origin = origin;
  if (origin == "blobSet") runData.blobs = helpers.getFromStorage("demoSet");
  if (origin == "upload") runData.inputs = clientApp.upload.getUploadedFiles();
  if ($("#crop-btn").is(":checked")) runData.crop_info = $("#editor-blob-left").cropper("getData");
}

function checkPostData() {
  if (!checkPostInputs()) return false;
  return true;
}

function checkPostInputs()  {
  if (helpers.getFromStorage("demoInfo").inputs.length != 0 && !helpers.getFromStorage("origin")) {
    errorMsg = "Input/s required."
    return false;
  }
  return true;
}

function enableRunButton() {
  $(".run-btn").prop('disabled', false);
  $(".run-btn").css('background-color', '#5d8cb1');
}

function hideRunningAnimation() {
  $(".loader").addClass('di-none');
  $(".loader").removeClass('element-appear');
}

function hideStatusContainer() {
  $(".run-msg-box").addClass('di-none');
}

function displayRunningAnimation() {
  $(".run-btn").prop('disabled', true);
  $(".run-btn").css('background-color', 'gray');
  $(".loader").removeClass('di-none');
  $(".loader").addClass('element-appear');
}

function displayError(msg) {
  $(".run-msg-box").removeClass('di-none');
  $(".run-msg-box").removeClass('run-success');
  $(".run-msg-box").addClass('element-appear');
  $(".run-msg-box").addClass('run-error');

  $(".run-msg").html(msg || errorMsg);
}

function displaySuccess(msg) {
  $(".run-msg-box").removeClass('di-none');
  $(".run-msg-box").removeClass('run-error');
  $(".run-msg-box").addClass('element-appear');
  $(".run-msg-box").addClass('run-success');

  $(".run-msg").html(msg);
}
