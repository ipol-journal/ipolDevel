var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};

var errorMsg = "Error.";
var runData;

$(".run-btn").click(function() {
  runDemo();
});

function runDemo() {
  runData = new FormData();
  setRunPostData();

  // si no lo tiene 30. si lo tiene lo que especifique.
  $.ajax({
      url: '/api/core/run2',
      type: 'POST',
      dataType: 'json',
      processData: false,
      contentType: false,
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
  runData.append("demo_id", demo_id);
  runData.append("params", JSON.stringify(params));
  if (origin) runData.append("origin", origin);
  if (origin == "blobSet") runData.append("blobs", JSON.stringify(helpers.getFromStorage("id_blobs")));
  if (origin == "upload") runData.append("blobs", JSON.stringify(getUploadedPostFiles()));
  if ($("#crop-btn").is(":checked")) runData.append("crop_info", JSON.stringify($("#editor-blob-left").cropper("getData")));
}

function getUploadedPostFiles(){
  var uploads = clientApp.upload.getUploadedFiles();
  var uploadsPost = {};
  for (let i = 0; i < Object.keys(uploads).length; i++) {
    uploadsPost["file_" + i] =  uploads[i];
  }
  return uploadsPost;
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
