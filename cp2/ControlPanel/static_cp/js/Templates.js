
let csrftoken = getCookie('csrftoken');
let section = document.querySelector('section');
let addTemplateDialog = document.querySelector('#addTemplate-dialog');
let template_id;

$(document).ready(function() {
    $("button#saveTemplate").click(addTemplates);
    $('#show').click(function (event) {
        if (typeof addTemplateDialog.showModal === "function") {
            addTemplateDialog.showModal();
        } else {
            showModal();
        }
        addTemplates();
    });
});

// Obsolete browser modal support...
function showModal(){
   var modalSelector = '#modal';
   $(modalSelector).html(`
      <h1 id="titleAddTemplate">Create new template</h1>
      <div id="templateForm">
         <label id="labelAddTemplate" required>Template name</label>
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

$('#addTemplate-dialog > .close').click(() => addTemplateDialog.close());

/*-----------------------------------------Request AJAX --------------------------------------------------------*/

function addTemplates() {
    $("button#saveTemplate").click(function () {
        templateName = $("#templateName").val();
        $.ajax({
            beforeSend: () => (templateName != ''),
            data : ({
                templateName : templateName,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            url: 'templates/ajax',
            dataType : 'json',
            success: function(data, responseText, xhr) {
                if (xhr.status == 200) {
                    document.location.href = `showTemplate?template_id=${data.template_id}&template_name=${templateName}`
                } else {
                    alert("Error when adding the template in the DataBase");
                }
            },
        })
    });
};
