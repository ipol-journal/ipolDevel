var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var demo_id = getParameterByName('demo_id');
var can_edit = document.getElementById('can_edit');

$(document).ready(function() {
    update_edit_demo();
    showDDL();
});

$("#changeThemeWhite").click(function() {
    aceEditor.setTheme("");
});

$("#changeThemeDark").click(function() {
    aceEditor.setTheme("ace/theme/tomorrow_night_blue");
});

var aceEditor = ace.edit("aceEditor", {
    mode: "ace/mode/json",
    autoScrollEditorIntoView: false,
    maxLines: 100,
    minLines: 20,
    height: '200px'
});


function update_edit_demo() {
    $.ajax({
        data: ({
            demoID: demo_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        dataType : 'json',
        type: 'POST',
        url: 'showDemo/ajax_user_can_edit_demo',
        success: function(data) {
            if (data.can_edit === 'NO') {
                var not_allowed = document.createElement('h3');
                not_allowed.textContent = "You are not allowed to edit this demo"
                can_edit.appendChild(not_allowed);
                $('#saveDDL').remove(); 

            }
        },
    });
};

function showDDL() {
    $.ajax({
        data: ({
            demoID: demo_id,
            csrfmiddlewaretoken: csrftoken,
        }),
        type: 'POST',
        dataType: 'json',
        url: 'showDemo/ajax_showDDL',
        success: function(data) {
            if (data.status === 'OK') {
                aceEditor.setValue(data.last_demodescription.ddl);
            } else {
                alert("Error to show the DDL of this Demo")
            }
        },
    });
};