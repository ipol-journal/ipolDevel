let demo_id = getParameterByName('demo_id');
let csrftoken = getCookie('csrftoken');
let buttons = document.getElementsByClassName('ddl');
let aceEditor = ace.edit("aceEditor", {
    mode: "ace/mode/json",
    autoScrollEditorIntoView: false,
    maxLines: 20,
    minLines: 20
});
aceEditor.setValue('{}');

let showDDL = function onClick() {
    let ddl = JSON.parse(this.getAttribute('data-ddl'));
    let creation = this.getAttribute('data-creation');
    let restoreButton = document.getElementById('restore-ddl-button');
    restoreButton.disabled = false;
    aceEditor.setValue(JSON.stringify(ddl, undefined, 2), -1);
};

Array.from(buttons).forEach(function(button) {
    button.addEventListener('click', showDDL);
  });

function saveDDL() {
    const ddl = aceEditor.getValue();
    $.ajax({
        beforeSend: function() {
            confirm('This will overwrite the current DDL for this demo, are you sure?');
        },
        data: ({
            demo_id: demo_id,
            ddl: ddl,
            csrfmiddlewaretoken: csrftoken,
        }),
        type: 'POST',
        dataType: 'json',
        url: 'ajax_save_DDL',
        success: function(data) {
            toast('DDL restored');
        },
        error: function(error) {
            
        }
    });

}