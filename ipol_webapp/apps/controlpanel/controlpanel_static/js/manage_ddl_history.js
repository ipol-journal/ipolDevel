
function showDDL(ddl, creationDate){
    ddl = ddl.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    document.getElementById("ddl").innerHTML=ddl;
    document.getElementById("title").innerHTML="DDL from: "+creationDate;
}

function restoreDDL(url, ddl, demo_id){
    var values = {
        'demo_id': demo_id,
        'ddl': ddl,
    }
    $.post(url, values, 'json');
    demo_url = "/cp/demo_edition/" + demo_id;
    window.location.href = demo_url;
}
