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
  fr.onload = function(e) { thumbnail_vr.src = this.result; };
  fr.readAsDataURL(vr.files[0]);
  if (vr.files.length > 0) {
      VRName = vr.files[0].name;
  }
  return VRImage = vr.files[0];
  return VRName;
};

function blobUploaded(){
  var thumbnail = document.getElementById("thumbnail");
  var blob = document.getElementById("Blob");
  var fr = new FileReader();
  fr.onload = function(e) { thumbnail.src = this.result; };
  fr.readAsDataURL(blob.files[0]);
  if (blob.files.length > 0) {
      blobName = blob.files[0].name;
  }
  return blobImage = blob.files[0];
};

function setBrokenImage(image) {
  image.onerror = "";
  image.src = "/cp2/static/images/non_viewable_inputs.png";
  return true;
}

//functions in demoinfo : 
//read_ddl(ddl_id) 
// read_demo(demo_id)
// get_ddl(demo_id)
// get_ddl_history(demo_id)
// get_interface_ddl(demo_id)
// read_ddl(ddl_id)

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