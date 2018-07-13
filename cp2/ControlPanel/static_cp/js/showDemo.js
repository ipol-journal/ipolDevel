var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var demo_id = getParameterByName('demo_id');
var can_edit = document.getElementById('can_edit');





$(document).ready(function() {
    var demo_list = new XMLHttpRequest();
    demo_list.open('GET', '/api/demoinfo/demo_list');
    demo_list.responseType = 'json';
    demo_list.send();
    demo_list.onload = function() {
        var data = demo_list.response;
        showDemoInformation(data['demo_list']);
    }
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
    maxLines: 20,
});
aceEditor.renderer.setScrollMargin(20, 20, 20, 20);


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
                document.getElementById('aceEditor').style.fontSize = '15px';
                aceEditor.setValue(data.last_demodescription.ddl);
            } else {
                alert("Error to show the DDL of this Demo")
            }
        },
    });
};

function showDemoInformation(demo_list) {
    for (var i = 0; i < demo_list.length; i++) {
        if (demo_list[i].editorsdemoid == demo_id){
            //console.log("modification="+demo_list[i].modification+"\neditorsdemoid="+demo_list[i].editorsdemoid+"\nstate="+demo_list[i].state+"\ncreation="+demo_list[i].creation+"\ntitle"+demo_list[i].title);
            document.getElementById("demo_id").innerHTML = demo_list[i].editorsdemoid;
            document.getElementById("title").innerHTML = demo_list[i].title;
            $("#demoExtras").attr('href', '/cp2/demoExtras?demo_id='+demo_id+"&title="+demo_list[i].title+"&modification="+demo_list[i].modification+"&state="+demo_list[i].state);
            $("#showBlobsDemo").attr('href', '/cp2/showBlobsDemo?demo_id='+demo_id);
        }
    };
};