var clientApp = clientApp || {};
var helpers = clientApp.helpers || {};

var errorMsg = "Error.";

$(".run-btn").click(function() {
  runDemo();
});

function runDemo() {
  $.ajax({
      url: '/api/core/run2',
      type: 'POST',
      dataType: 'json',
      beforeSend: function(){
        hideRunningAnimation();
        displayRunningAnimation();
        return checkPostData();
      },
      data: {
        "demo_id": demo_id,
        "params": params
        // "origin":
        // "crop_info"

      }
    })
    .done(function(res) {
      console.log(res);
      displaySuccess("Success!");
      //Call drawResults function
    })
    .fail(function(res) {
      console.log(res);
      displayError(res.responseText);
      //Show back-end error messages
    })
    .always(function() {
      hideRunningAnimation();
      enableRunButton();
    });
}

function checkPostData(){
  if(!checkPostInputs()) return false;
  return true;
}

function checkPostInputs() {
  if(helpers.getFromStorage("demoInfo").inputs.length != 0 && !helpers.getFromStorage("origin")){
    errorMsg = "Input/s required."
    return false;
  }
  return true;
}

function enableRunButton(){
  $(".run-btn").prop('disabled', false);
  $(".run-btn").css('background-color', '#5d8cb1');
}

function hideRunningAnimation(){
  $(".loader").addClass('di-none');
  $(".loader").removeClass('element-appear');
}

function hideStatusContainer(){
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

  $(".run-msg").html(msg || errorMsg);
}

function displaySuccess(msg) {
  $(".run-msg-box").removeClass('di-none');
  $(".run-msg-box").removeClass('run-error');
  $(".run-msg-box").addClass('element-appear');
  $(".run-msg-box").addClass('run-success');

  $(".run-msg").html(msg);
}
