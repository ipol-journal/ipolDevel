// toggle the visibility of an element
function toggle(id) {
  var element=document.getElementById(id);
  if(element.style.display == "none" ) {
    element.style.display = "";
  }
  else {
    element.style.display = "none";
  }
  return false;
}

