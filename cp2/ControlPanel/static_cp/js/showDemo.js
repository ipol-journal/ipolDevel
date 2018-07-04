var section = document.querySelector('section');
var csrftoken = getCookie('csrftoken');
var demo_id = getParameterByName('demo_id');
var title = getParameterByName('title');
var modification = getParameterByName('modification');
var state = getParameterByName('state');
document.getElementById("demo_id").innerHTML = demo_id;
document.getElementById("title").innerHTML = title;
$("#showBlobsDemo").attr('href', '/cp2/showBlobsDemo?demo_id='+demo_id+"&title="+title+"&modification="+modification+"&state="+state);
$("#demoExtras").attr('href', '/cp2/demoExtras?demo_id='+demo_id+"&title="+title+"&modification="+modification+"&state="+state);



$(document).ready(function() {
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
    autoScrollEditorIntoView: true,
    maxLines: 20,
});
editor2.renderer.setScrollMargin(20, 20, 20, 20);




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
                var demoString = JSON.stringify(data.last_demodescription);
                document.getElementById('editor2').style.fontSize = '15px';
                editor2.setValue(data.last_demodescription.ddl);
            } else {
                alert("Error to show the DDL of this Demo")
            }
        },
    });
};