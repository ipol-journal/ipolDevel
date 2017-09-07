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

  $.ajax({
      url: '/api/core/run2',
      type: 'POST',
      processData: false,
      contentType: false,
      cache: false,
      beforeSend: function() {
        hideRunningAnimation();
        hideStatusContainer();
        displayRunningAnimation();
        return checkPostData();
      },
      data: runData
    })
    .done(function(res) {
      if (res.status == "KO") displayError(res.error, "server");
      else {
        displaySuccess("Execution successful");
        updateURL(res);
        results.draw(res);
      }
    })
    .fail(function(res) {
      displayError(res.responseText, "client");
    })
    .always(function(res) {
      console.log(res);
      hideRunningAnimation();
      enableRunButton();
    });
}

function updateURL(run_response){
  var url = window.location.href;
  if(url.includes('&key')) url = url.split("&")[0];
  window.history.pushState({'result': run_response, 'params': params, 'origin': helpers.getFromStorage("origin") }, null, url + "&key=" + run_response.key);
}

function setRunPostData() {
  var origin = helpers.getFromStorage("origin");
  runData.append("demo_id", demo_id);
  runData.append("params", JSON.stringify(params));
  if (origin) runData.append("origin", origin);
  if (origin == "blobSet") runData.append("blobs", JSON.stringify(helpers.getFromStorage("id_blobs")));
  if (origin == "blobSet") runData.append("setId", JSON.stringify(helpers.getFromStorage("setId")));
  if (origin == "upload" && !($("#crop-btn").is(":checked"))) setUploadedFiles();
  if (origin == "upload" && $('#privateSwitch').is(":checked")) runData.append("private_mode", true);
  if ($("#crop-btn").is(":checked")) checkCropper();
}

function setUploadedFiles() {
  var uploads = clientApp.upload.getUploadedFiles();
  for (let i = 0; i < Object.keys(uploads).length; i++) {
    runData.append("file_" + i, files[i]);
  }
}

function checkCropper() {
  var origin = helpers.getFromStorage("origin");
  if (origin == "blobSet") runData.append("crop_info", JSON.stringify($("#editor-blob-left").cropper("getData")));
  if (origin == "upload") runData.append('file_0', helpers.base64ToBlob($("#editor-blob-left").cropper("getCroppedCanvas").toDataURL()));
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
  $(".run-btn").removeClass('disable-btn');
}

function hideRunningAnimation() {
  $(".loader").addClass('di-none');
  $(".loader").removeClass('element-appear');
}

function hideStatusContainer() {
  $(".msg-box").addClass('di-none');
}

function displayRunningAnimation() {
  $(".run-btn").prop('disabled', true);
  $(".run-btn").addClass('disable-btn');
  $(".loader").removeClass('di-none');
  $(".loader").addClass('element-appear');
}

function displayError(msg, origin) {
  $(".msg-box").removeClass('di-none');
  $(".msg-box").removeClass('run-success');
  $(".msg-box").addClass('element-appear');
  $(".msg-box").addClass('run-error');
  if(origin == "server") $('.msg-box').addClass('server-error');
  $(".run-msg").html(msg || errorMsg);
}

function displaySuccess(msg) {
  $(".msg-box").removeClass('di-none');
  $(".msg-box").removeClass('run-error');
  $(".msg-box").addClass('element-appear');
  $(".msg-box").addClass('run-success');

  $(".run-msg").html(msg);
}
