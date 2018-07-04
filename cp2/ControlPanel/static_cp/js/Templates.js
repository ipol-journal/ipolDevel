
//Middleware rapport voir doc Django => Intergiciel
// bug in the old CP, you can add a template without a name and it bug all the list of templates 
// same with a space in the name of the new template
/*-----------------------------------------Variables-----------------------------------------*/

var csrftoken = getCookie('csrftoken');
var section = document.querySelector('section');
var request = new XMLHttpRequest();
var templateSelection;
/*-----------------------------------------Templates and add Templates-----------------------------------------*/

request.open('GET', '/api/blobs/get_all_templates');
request.responseType = 'json';
request.send();
request.onload = function() {
    var templates = request.response;
    templatesList = templates['templates'];
    showTemplatesList(templates);
}

$(document).ready(function() {
    $("button#saveTemplate").click(addTemplates);
    $('#show').click(function (event) {
        //On désactive le comportement du lien
        event.preventDefault();
        showModal();
        addTemplates();
    });
    $(window).resize(function () {
        resizeModal()
   });
});

/*-----------------------------------------JS Functions-----------------------------------------*/

function showTemplatesList (jsonObj) {
    var templatesList = jsonObj['templates'];
    for (var i=0; i < templatesList.length; i++){
        var myArticle = document.createElement('article');
        var myHref = document.createElement('a');
        myHref.setAttribute("href","/cp2/showTemplates?template="+templatesList[i]);
        myHref.textContent = templatesList[i];

        myArticle.appendChild(myHref);
        section.appendChild(myArticle);
    };
}

function showModal(){
   var id = '#modal';
   $(id).html('<a id="titleAddTemplate">Add a new template</a></br><label id="labelAddTemplate">Template name </label><input type="text" id="Template_name"/></br> <button class="close">Close</button> <button id="saveTemplate">Save</button>');
   
   resizeModal();
   
   // Effet de transition     
   $('#fond').fadeIn(1000);   
   $('#fond').fadeTo("slow",0.7);
   // Effet de transition   
   $(id).fadeIn(2000);
   
   $('.popup .close').click(function (e) {
      // On désactive le comportement du lien
      e.preventDefault();
      // On cache la fenetre modale
      hideModal();
    });
}

function resizeModal(){
   var modal = $('#modal');
   // On récupère la largeur de l'écran et la hauteur de la page afin de cacher la totalité de l'écran
   var winH = $(document).height();
   var winW = $(document).width();
   
   // le fond aura la taille de l'écran
   $('#fond').css({'width':winW,'height':winH});
   
   // On récupère la hauteur et la largeur de l'écran
   // On met la fenêtre modale au centre de l'écran
   modal.css('top', winH/2 - modal.height()/2);
   modal.css('left', winW/2 - modal.width()/2);
}

function hideModal(){
   // On cache le fond et la fenêtre modale
   $('#fond, .popup').hide();
   $('.popup').html('');
}

/*-----------------------------------------Request AJAX as a JS function-----------------------------------------*/

//authenticate
function addTemplates() {
    $("button#saveTemplate").click(function () {
        $nameTemplate = $("#Template_name").val();
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
                    alert("Successful ! Redirection ...");
                    document.location.href = "/cp2/templates"
                } else {
                    alert("Error to add the template in the DataBase");
                }
            },
        })
    });
};
