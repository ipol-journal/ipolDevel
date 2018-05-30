function deleteBlob(url,id,set,pos){
    var values = {'demo_id': id,'set': set,'pos': pos};
    $.post(url, values, 'json')
    .done(function() {
      console.log("Success");
    })
    .fail(function() {
      // this is a patch to work with firefox/safari
      window.location.reload(true);
    });
}

function removeTemplateFromDemo(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json')
    .done(function () {
        console.log("Success");
    })
    .fail(function ()  {
        // this is a patch to work with firefox/safari
        window.location.reload(true);
    });
}
function addTemplateToDemo(url,id,template){
    var values = {'demo_id': id,'template': template};
    $.post(url, values, 'json')
    .done(function () {
        console.log("Success");
    })
    .fail(function ()  {
        // this is a patch to work with firefox/safari
        window.location.reload(true);
    });
}
