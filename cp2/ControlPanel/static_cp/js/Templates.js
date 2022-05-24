
/*-----------------------------------------Variables-----------------------------------------*/

var csrftoken = getCookie('csrftoken');
var section = document.querySelector('section');
var template_id;
/*-----------------------------------------Templates and add Templates-----------------------------------------*/


$(document).ready(function() {
    var get_demo_blobs = new XMLHttpRequest();
    get_demo_blobs.open('GET', '/api/blobs/get_all_templates');
    get_demo_blobs.responseType = 'json';
    get_demo_blobs.send();
    get_demo_blobs.onload = function() {
        var templates = get_demo_blobs.response;
        templatesList = templates['templates'];
        showTemplatesList(templatesList);
    }
    $("button#saveTemplate").click(addTemplates);
    $('#show').click(function (event) {
        event.preventDefault();
        showModal();
        addTemplates();
    });
});

/*-----------------------------------------JS Functions-----------------------------------------*/

function showTemplatesList (templatesList) {
    for (var i=0; i < templatesList.length; i++){
        var templates = document.createElement('article');
        var templateName = document.createElement('a');
        templateName.setAttribute("href",`/cp2/showTemplate?template_id=${templatesList[i].id}&template_name=${templatesList[i].name}`);
        templateName.textContent = templatesList[i].name;
        templates.appendChild(templateName);
        $('#template-container').append(templates);
    };
}

function showModal(){
   var modalSelector = '#modal';
   $(modalSelector).html(`
      <h1 id="titleAddTemplate">Create new template</h1>
      <div id="templateForm">
         <label id="labelAddTemplate">Template name</label>
         <input type="text" id="templateName"/>
      </div>
      <button id="saveTemplate" class="btn">Save</button>
      <button class="btn close">Close</button>`);

   $('#fond').fadeIn(1000);   
   $('#fond').fadeTo("slow",0.7);
   $(modalSelector).fadeIn(1000);

   $('.popup .close').click(function (e) {
      e.preventDefault();
      hideModal();
    });
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}

/*-----------------------------------------Request AJAX --------------------------------------------------------*/

function addTemplates() {
    $("button#saveTemplate").click(function () {
        templateName = $("#templateName").val();
        $.ajax({
            beforeSend: function(xhr, settings) {
                if (templateName == ''){
                    return false
                }
                else {
                    return true
                }
            },
            data : ({
                templateName : templateName,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            url: 'templates/ajax',
            dataType : 'json',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = `/cp2/showTemplates?template_id=${data.template_id}&template_name=${templateName}`
                } else {
                    alert("Error when adding the template in the DataBase");
                }
            },
        })
    });
};
