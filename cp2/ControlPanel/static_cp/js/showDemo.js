let section = document.querySelector('section');
let csrftoken = getCookie('csrftoken');
let demo_id = getParameterByName('demo_id');
let can_edit = document.getElementById('can_edit');
let saveButton = document.getElementById("save-btn");
let ddlStatusText = document.getElementById("ddl-status-text");
let editorsDialog = document.querySelector('#editors-dialog');
const editorsButton = document.getElementById('editors-btn');
let aceEditor = ace.edit("aceEditor", {
	 mode: "ace/mode/json",
	 autoScrollEditorIntoView: false,
	 maxLines: 100,
	 minLines: 20
});
aceEditor.setValue('{}');
let last_DDL_saved = aceEditor.getValue();
let editors = '';

$(document).ready(function() {
	 showDDL();
	 aceEditor.on('input', function(){
		console.log('input');
		checkChanges();
	})
});

$('#editors-btn-close').click(() => editorsDialog.close());

// Ace editor THEMES
$("#changeThemeWhite").click(function() {
	 aceEditor.setTheme("");
});

$("#changeThemeDark").click(function() {
	 aceEditor.setTheme("ace/theme/tomorrow_night_blue");
});

// Save shortcut keybind
aceEditor.commands.addCommand({
	 name: 'save',
	 bindKey: { win: "Ctrl-S", "mac": "Cmd-S" },
	 exec: saveDDL
});

// check for unsaved changes in the DDL, and show a message in that case
function checkChanges(){
    // compare the last saved DDL with the current DDL in the editor
    if (last_DDL_saved.localeCompare(aceEditor.getValue()) != 0){
        saveButton.disabled = false;
        DDLStatusMessage('', 'There are unsaved changes.');
    }else{
        saveButton.disabled = true;
        DDLStatusMessage('', 'DDL already saved.');
    }
}

// Save DDL in case of changes
function saveDDL() {
    if (last_DDL_saved.localeCompare(aceEditor.getValue()) != 0) validateJSON()
}

// validate JSON DDL, and submit via AJAX if it is OK
function validateJSON(){
    saveButton.disabled = true;

    let DDLJSON = aceEditor.getSession().getAnnotations().length;
    let editor_value = aceEditor.getValue();
	
    // >0 if errors found, ==0 if JSON is OK
    // check syntax and it is not empty
    if (DDLJSON == 0 && editor_value != ''){
        // DDLStatusMessage('', 'Saving...');
        submitDDL();
        saveButton.disabled = false;
    }else{
        // show message to indicate errors
        DDLStatusMessage('KO', 'DDL not saved, please check the syntax.');
        saveButton.disabled = false;
    }
}

function submitDDL() {
	const ddl = aceEditor.getValue();
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
			DDLStatusMessage('', 'DDL saved.');
			toast('DDL saved');
		},
		error: function(error) {
			console.log('Error');
		}
	});
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

function DDLStatusMessage(status, text) {
	if (status == 'KO') {
		ddlStatusText.style.color = 'red';
	} else if (status == 'OK') {
		ddlStatusText.style.color = 'green';
	} else {
		ddlStatusText.style.color = 'black';
	}
	ddlStatusText.innerHTML = text;
}

$(window).bind('beforeunload', function (e) {
    if (last_DDL_saved.localeCompare(aceEditor.getValue()) != 0) return 'DDL changes made but not saved. Are you sure you want to leave?';
});

// Demo editors dialog
editorsButton.addEventListener('click', function onOpen() {
	if (typeof editorsDialog.showModal === "function") {
		 editorsDialog.showModal();
	} else {
	   outputBox.value = "Sorry, the <dialog> API is not supported by this browser.";
	}
 });

$('.editor > button').click(function() {
   let editor_id = $(this).attr('data-editor-id');
   $.ajax({
	   data: ({
		   demo_id: demo_id,
		   editor_id: editor_id,
		   csrfmiddlewaretoken: csrftoken,
	   }),
	   type: 'POST',
	   dataType: 'json',
	   url: 'remove_demo_editor',
	   success: function(data) {
		   if (data.status == 'OK') {
			   $(`#editor-${editor_id}`).remove();
		   } else {
			   alert(`Editor could not be removed. ${data.message}`)
		   }
	   },
	   error: function(error) {
		   alert(`Editor could not be removed. ${error}`)
	   }
   });
})