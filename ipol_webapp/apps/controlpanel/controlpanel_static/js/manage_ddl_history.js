//Editor configuration
editor = ace.edit("editor");
editor.getSession().setMode("ace/mode/json");
editor.getSession().setUseWrapMode(true);
editor.getSession().setTabSize(4);
editor.setAutoScrollEditorIntoView(true);

editor.setOptions({
    readOnly: true,
    highlightActiveLine: false,
    highlightGutterLine: false
})
editor.renderer.$cursorLayer.element.style.opacity=0

selected_ddl = null

function showDDL(ddl, creationDate){
    selected_ddl=ddl
    editor.setValue(ddl);
    editor.gotoLine(0);
    document.getElementById("title").innerHTML="DDL from: "+creationDate;
}

function restoreDDL(url, demo_id){
    var values = {
        'demo_id': demo_id,
        'ddl': selected_ddl,
    }
    $.post(url, values, 'json');
    demo_url = "/cp/demo_edition/" + demo_id;
    window.location.href = demo_url;
}

