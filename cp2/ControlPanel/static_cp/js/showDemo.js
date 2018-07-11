var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var demo_id = getParameterByName('demo_id');
var can_edit = document.getElementById('can_edit');
var demo_list = new XMLHttpRequest();
demo_list.open('GET', '/api/demoinfo/demo_list');
demo_list.responseType = 'json';
demo_list.send();
demo_list.onload = function() {
    var data = demo_list.response;
    demoInformation(data['demo_list']);
}





$(document).ready(function() {
    update_edit_demo();
    showDDL();
});

$("#changeThemeWhite").click(function() {
    editor2.setTheme("");
});

$("#changeThemeDark").click(function() {
    editor2.setTheme("ace/theme/tomorrow_night_blue");
});

var editor2 = ace.edit("editor2", {
    mode: "ace/mode/json",
    autoScrollEditorIntoView: false,
    maxLines: 20,
});
editor2.renderer.setScrollMargin(20, 20, 20, 20);


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
                document.getElementById('editor2').style.fontSize = '15px';
                editor2.setValue(data.last_demodescription.ddl);
            } else {
                alert("Error to show the DDL of this Demo")
            }
        },
    });
};

function demoInformation(demo_list) {
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