
/*-----------------------------------------Variables-----------------------------------------*/

var csrftoken = getCookie('csrftoken');
var section = document.querySelector('section');
var templateSelection;
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
    $(window).resize(function () {
        resizeModal()
   });
});

/*-----------------------------------------JS Functions-----------------------------------------*/

function showTemplatesList (templatesList) {
    for (var i=0; i < templatesList.length; i++){
        var templates = document.createElement('article');
        var templateName = document.createElement('a');
        templateName.setAttribute("href","/cp2/showTemplates?template="+templatesList[i]);
        templateName.textContent = templatesList[i];
        templates.appendChild(templateName);
        section.appendChild(templates);
    };
}

function showModal(){
   var id = '#modal';
   $(id).html('<a id="titleAddTemplate">Add a new template</a></br><label id="labelAddTemplate">Template name </label><input type="text" id="templateName"/></br> <button class="close">Close</button> <button id="saveTemplate">Save</button>');
   
   resizeModal();
   
   $('#fond').fadeIn(1000);   
   $('#fond').fadeTo("slow",0.7);
   $(id).fadeIn(1000);
   
   $('.popup .close').click(function (e) {
      e.preventDefault();
      hideModal();
    });
}

function resizeModal(){
   var modal = $('#modal');
   var winH = $(document).height();
   var winW = $(document).width();
   
   $('#fond').css({'width':winW,'height':winH});
   
   modal.css('top', winH/2 - modal.height()/2);
   modal.css('left', winW/2 - modal.width()/2);
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}

/*-----------------------------------------Request AJAX --------------------------------------------------------*/

function addTemplates() {
    $("button#saveTemplate").click(function () {
        $nameTemplate = $("#templateName").val();
        $.ajax({
            beforeSend: function(xhr, settings) {
                if ($nameTemplate == ''){
                    return false
                }
                else {
                    return true
                }
            },
            data : ({
                nameTemplate : $nameTemplate,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            url: 'templates/ajax',
            dataType : 'json',
            success: function(data) {
                if (data.status === 'OK') {
                    document.location.href = "/cp2/templates"
                } else {
                    alert("Error to add the template in the DataBase");
                }
            },
        })
    });
};
