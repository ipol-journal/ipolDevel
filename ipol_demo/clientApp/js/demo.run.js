var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};

var errorMsg = 'Error.';
var runData;
var clientData;

$('.run-btn').click(function() {
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
      hideStatusContainer();
      displayRunningAnimation();
      return checkPostData();
    },
    data: runData
  })
  .done(function(res) {
    if (res.status === 'KO') {
      $('.results').addClass('di-none');
      $('.results-container').empty();
      displayError(res.error, 'server');
    }else {
      displaySuccess();
      updateURL(res);
      results.draw(res);
    }
  })
  .fail(function(res) {
    displayError(res.responseText, 'client');
  })
  .always(function(res) {
    console.log(res);
    hideRunningAnimation();
    enableRunButton();
  });
}

function updateURL(run_response){
  var url = window.location.href;
  if (getParameterByName('key')) url = url.split('&')[0];
  if (getParameterByName('archive')) url = url.split('&')[0];
  
  window.history.pushState({}, null, url + '&key=' + run_response.key);
}

function setRunPostData() {
  clientData = {};
  clientData.demo_id = parseInt(demo_id);
  clientData.params = params;
  
  var origin = helpers.getFromStorage('origin');
  if (origin) clientData.origin = origin;
  if (origin === 'blobSet'){
    clientData.blobs = helpers.getFromStorage('id_blobs');
    clientData.setId = helpers.getFromStorage('setId');
  } 
  if (origin === 'upload'){
    if ($('#privateSwitch').is(':checked')) clientData.private_mode = true;
    setUploadedFiles();
  } 

  checkCropper();
  runData.append('clientData', JSON.stringify(clientData));
}

function setUploadedFiles() {
  var uploads = clientApp.upload.getUploadedFiles();
  for (let i = 0; i < Object.keys(uploads).length; i++)
    runData.append('file_' + i, files[i], files[i].name);
}

function checkCropper() {
  if ($('#crop-btn').is(':checked')) 
    clientData.crop_info = $('#editor-blob-left').cropper('getData');
}

function checkPostData() {
  if (!checkPostInputs()) return false;
  if ($('#crop-btn').is(':checked') && !validCrop()) return false
  return true;
}

function checkPostInputs()  {
  if (helpers.getFromStorage('demoInfo').inputs && helpers.getFromStorage('demoInfo').inputs.length != 0 && !helpers.getFromStorage('origin')) {
    errorMsg = 'Input/s required.'
    return false;
  }
  return true;
}

function validCrop()  {
  var cropData = $('#editor-blob-left').cropper('getCroppedCanvas');
  if (cropData.width * cropData.height === 0) {
    errorMsg = 'Cropped image is too small.'
    return false;
  }
  return true;
}

function enableRunButton() {
  $('.run-btn').prop('disabled', false);
  $('.run-btn').removeClass('disable-btn');
}

function hideRunningAnimation() {
  $('.loader').addClass('di-none');
  $('.loader').removeClass('element-appear');
}

function hideStatusContainer() {
  $('.msg-box').addClass('di-none');
}

function displayRunningAnimation() {
  $('.run-btn').prop('disabled', true);
  $('.run-btn').addClass('disable-btn');
  $('.loader').attr('class', 'loader element-appear');
}

function displayError(msg, origin) {
  $('.msg-box').attr('class', 'msg-box element-appear run-error')
  if(origin === 'server') $('.msg-box').addClass('server-error');
  $('.run-msg').html(msg || errorMsg);
}

function displaySuccess() {
  $('.msg-box').attr('class', 'msg-box element-appear run-success')
  $('.run-msg').html('Execution successful');
}
