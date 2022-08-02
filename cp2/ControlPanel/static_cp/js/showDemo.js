let section = document.querySelector('section');
let csrftoken = getCookie('csrftoken');
let demo_id = getParameterByName('demo_id');
let title = getParameterByName('title');
let can_edit = document.getElementById('can_edit');
const location_url = `${window.location.protocol}//${window.location.host}`;
let saveButton = document.getElementById("save-btn");
let ddlStatusText = document.getElementById("ddl-status-text");
let editorsDialog = document.querySelector('#editors-dialog');
const editorsButton = document.getElementById('editors-btn');

let demoEditDialog = document.querySelector('#editDemo-dialog');
const demoEditButton = document.getElementById('demoEdit-btn');

let aceEditor = ace.edit("aceEditor", {
	 mode: "ace/mode/json",
	 autoScrollEditorIntoView: false,
	 minLines: 100
});
aceEditor.setValue('{}');
let last_DDL_saved = aceEditor.getValue();
let editors = '';

$(document).ready(function() {
	 showDDL();
	 aceEditor.on('input', function(){
		checkChanges();
	})
	get_demos();
	getDemoState();
});

$('#editors-btn-close').click(() => editorsDialog.close());
$('#demoEdit-btn-close').click(() => demoEditDialog.close());

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
			toast('Error when saving DDL, try again');
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
				toast(`Error: ${data.error}`);
				aceEditor.setValue({}, -1);
				last_DDL_saved = aceEditor.getValue();
			}
		},
		error: function(error) {
			toast('Error getting DDL, please reload or contact support');
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
		window.location.href = `demo_editors?demo_id=${demo_id}&title=${title}`;
	}
 });

 demoEditButton.addEventListener('click', function onOpen() {
	if (typeof demoEditDialog.showModal === "function") {
		 demoEditDialog.showModal();
	} else {
		showDemoEditModal();
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

async function get_demos() {
	demo_ids = await fetch(`${location_url}/api/demoinfo/demo_list`)
		.then(response => response.json())
		.then(data => {
			let ids = data.demo_list.map(demo => demo.editorsdemoid);
			return ids;
		});

	$('#new_demo_id').keyup(function() {
		const value = $(this).val();
		let inputID = document.getElementById('new_demo_id');
		if (value == demo_id) {
			inputID.setCustomValidity('');
			return;
		}
		let demoIDtext = document.getElementById('demo-id-used-warning');
		if (value.length == 0) {
			demoIDtext.innerHTML = '';
			return;
		}
		const contained = demo_ids.includes(parseInt(value));
		if (contained && value != demo_id) {
			inputID.setCustomValidity('ID in use, pick another');
			demoIDtext.innerHTML = 'ID in use, pick another';
			demoIDtext.style.color = "red";
		} else {
			inputID.setCustomValidity('');
			demoIDtext.innerHTML = 'Demo ID is valid';
			demoIDtext.style.color = "green";
		}
	});
}

async function getDemoState() {
	let demoMetadata = await fetch(`${location_url}/api/demoinfo/read_demo_metainfo?demoid=${demo_id}`)
	.then(response => response.json())
	$(`option[value=${demoMetadata.state}]`)
	document.querySelector(`option[value=${demoMetadata.state}]`).selected = true;
}

function deleteDemo() {
	$.ajax({
		beforeSend: function() {
			return confirm('This will permanently delete the current demo, are you sure?');
		},
		data: ({
			demo_id: demo_id,
			csrfmiddlewaretoken: csrftoken,
		}),
		dataType : 'json',
		type: 'POST',
		url: 'removeDemo/ajax',
		success: function(data) {
			if (data.status != 'OK') {
				toast(data.message);
			} else {
				toast('Demo deleted successfully');
				document.location.href = `/cp2/`
			}
		},
   });
}

function showDemoEditModal() {
	let id = '#modal';
	$(id).html(`
		<h1>Edit demo</h1>
		<form id="edit-demo-form" action="showDemo/ajax_edit_demo" autocomplete="off" method="post" enctype="multipart/form-data">
			<input type="hidden" name="csrfmiddlewaretoken" value="${csrftoken}">
			<input type="hidden" name="demo_id" value="${demo_id}">
			<label for="demoID">Demo ID</label>
			<input type="number" name="new_demo_id" id="new_demo_id" value="${demo_id}" min="1" required>
			<p id="demo-id-used-warning"></p>
			<label for="demoTitle">Title</label>
			<input type="text" name="demoTitle" value="${title}" required>
			<label for="state">State</label>
			<select name="state" id="state-select">
				<option value="test">test</option>
				<option value="workshop">workshop</option>
				<option value="preprint">Preprint</option>
				<option value="published">Published</option>
			</select>
			<input type="submit" name="save-demo-submit" class="btn btn-save" value="Save">
		</form>
		<button id="delete-demo-btn" class="btn btn-danger" onclick="deleteDemo()">Delete demo</button>
		<button id="demoEdit-btn-close" class="btn btn-delete dialog-btn-close">X</button>
	`);

	$('#fond').fadeIn(500)   
	$('#fond').fadeTo("slow",0.7);
	$(id).fadeIn(300);
	$('.popup .demoEdit-btn-close').click(function (event) {
		event.preventDefault();
		hideModal();
	});
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}

function copyKey() {
	const key = document.getElementById('ssh-key');
	navigator.clipboard.writeText(key.textContent);
	toast('Ssh key copied to clipboard.');
}
