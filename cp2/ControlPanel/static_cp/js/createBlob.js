var VRImage;
var csrftoken = getCookie('csrftoken');
var blobImage;
var templateSelection = getParameterByName('template');
document.getElementById("nameOfTemplate").innerHTML = templateSelection;
$("#GoPreviousPage").attr('href', '/cp2/showTemplates?template='+templateSelection);
var form = document.getElementById('createBlobForm');
form.onsubmit = function (e) {
    e.preventDefault();
    var formData = new FormData();
    formData.append('Title', $('#Title').val());
    formData.append('SET' , $('#SET').val());
    formData.append('PositionSet', $('#PositionSet').val());
    formData.append('Credit', $('#Credit').val());
    formData.append('Tags', $('#Tags').val());
    formData.append('TemplateSelection', templateSelection);
    formData.append('Blobs', blobImage, blobImage.name);
    if (VRImage) {
        formData.append('VR', VRImage, VRImage.name);
    }
    formData.append('csrfmiddlewaretoken', csrftoken );
    $.ajax({
        url: 'createBlob/ajax',
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        type: 'POST',
        dataType : 'json',
        success: function(data) {
            if (data.status === 'OK') {
                alert("Redirection Templates List...")
                document.location.href = "/cp2/showTemplates?template="+templateSelection
            } else {
                alert("Error to add this Blob to the Template")
            }
        },
    })
};