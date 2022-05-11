var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var demo_id = getParameterByName('demo_id');
var can_edit = document.getElementById('can_edit');
let saveButton = document.getElementById("save-btn");
let aceEditor = ace.edit("aceEditor", {
    mode: "ace/mode/json",
    autoScrollEditorIntoView: false,
    maxLines: 100,
    minLines: 20
});
aceEditor.setValue('{}');
var last_DDL_saved = aceEditor.getValue();

$(document).ready(function() {
    showDDL();
    ddlModified();
    // update_edit_demo();
});

$("#changeThemeWhite").click(function() {
    aceEditor.setTheme("");
});

$("#changeThemeDark").click(function() {
    aceEditor.setTheme("ace/theme/tomorrow_night_blue");
});

aceEditor.on('input', function(){
    saveButton.disabled = aceEditor.session.getUndoManager().isClean();
    ddlModified();
})

// Save shortcut keybind
aceEditor.commands.addCommand({
    name: 'save',
    bindKey: { win: "Ctrl-S", "mac": "Cmd-S" },
    exec: saveDDL
});

$("#save-btn").click(saveDDL);

function saveDDL() {
    const ddl = aceEditor.getValue();
    if (last_DDL_saved.localeCompare(ddl) != 0) {
        $.ajax({
            data: ({
                demo_id: demo_id,
                ddl: ddl,
                csrfmiddlewaretoken: csrftoken,
            }),
            type: 'POST',
            dataType: 'json',
            url: 'showDemo/ajax_save_DDL',
            success: function(data) {
                aceEditor.session.getUndoManager().markClean();
                saveButton.disabled = aceEditor.session.getUndoManager().isClean();
                last_DDL_saved = aceEditor.getValue();
                ddlModified();
            },
            error: function(error) {
                
            }
        });
    }

}


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
            if (!data.can_edit) {
                $('#save-btn').addClass('btn-disabled');
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
                aceEditor.setValue(data.last_demodescription.ddl, -1);
                last_DDL_saved = aceEditor.getValue();
                aceEditor.session.getUndoManager().markClean();

            } else {
                aceEditor.setValue({});
                last_DDL_saved = aceEditor.getValue();

            }
        },
        error: function(error) {
            alert('Error getting DDL, please reload or contact support')
        }
    });
};

function ddlModified() {
    if (aceEditor.session.getUndoManager().isClean()) {
        $('#saved-text').removeClass('di-none');
        $('#not-saved-text').addClass('di-none');
    } else {
        $('#saved-text').addClass('di-none');
        $('#not-saved-text').removeClass('di-none');
    }
}
