function getParameterByName(name) {
    var url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
    results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
  };
  
function vrUploaded(){
  var thumbnail = document.getElementById("thumbnail_vr");
  var vr = document.getElementById("VR");
  var fr = new FileReader();
  fr.onload = function() { thumbnail.src = this.result; };
  fr.readAsDataURL(vr.files[0]);
  if (vr.files.length > 0) {
    document.getElementById("thumbnail_vr").style = "visibility : visible";
    VRName = vr.files[0].name;
  }
  return VRImage = vr.files[0];
};

function blobUploaded(){
  var thumbnail = document.getElementById("thumbnail");
  var blob = document.getElementById("Blob");
  var fr = new FileReader();
  fr.onload = function() { thumbnail.src = this.result; };
  fr.readAsDataURL(blob.files[0]);
  if (blob.files.length > 0) {
    blobName = blob.files[0].name;
  }
  return blobImage = blob.files[0];
};

function removeBlob(){
  document.getElementById("Blob").value = "";
  document.getElementById("thumbnail").src = "";
  blobImage = null;
}

function removeVr(){
  document.getElementById("VR").value = "";
  document.getElementById("thumbnail_vr").src = "";
  VRImage = null;
}

function setBrokenImage(image) {
  image.onerror = "";
  image.src = "/cp2/static/images/non_viewable_inputs.png";
}

/*  secure AJAX POST to ws ,from django docs  */
function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

// function update_edit_demo() {
//   $.ajax({
//       data: ({
//           demoID: demo_id,
//           csrfmiddlewaretoken: csrftoken,
//       }),
//       dataType : 'json',
//       type: 'POST',
//       url: 'showDemo/ajax_user_can_edit_demo',
//       success: function(data) {
//           if (data.can_edit === 'NO') {
//               console.log("gagner");
//           }
//       },
//   });
// };



// function templatesList_not_used(Array1, Array2){
//     for (var i=0; i< Array1.length; i++){
//         for(var j=0; j< Array2.length; j++){
//             if (Array1.includes(Array2[j])){
//                 Array1.splice(i,1); 
//             }
//         }
//     }
//     return Array1;
// }


//mettre tout le JS ds ce repertoire avec le nom des pages dependante HTML
//exemple homepgae.js
//exemple loginpage.js
//Remove green code
//faire de meme avec le CSS (que le JS)
//homepage.css
//centrer les elements
// exemple homepage avec list of demos
//meme style pour les boutons 
//codepen pour l'inspiration du CSS



