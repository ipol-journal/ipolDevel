/*
//console.log(myshdwnurl);
function send_archive_shutdown_request() {
    var confirmshutdown = confirm(' Dou You Want to shutdown Archive Module?');
    if (confirmshutdown == true) {

        $.ajax({
            type: 'GET',
            url: myshdwnurl,
            dataType: 'json',
            success: function (data) {
                //console.error(data.status);
                var okhtml = "<p class=\"ststsnok\">Archive Module Shutdown successfull</p>";
                $('#archive_module_info').html(okhtml);
            },
            error: function (data) {
                var errorhtml = "<p>Could not shutdown properly, refresh page</p>";
                $('#archive_module_info').html(errorhtml);
            }
        });
    }
}


function send_add_test_to_test_demo(wsurl) {
    var addexp = confirm('Add exp to test demo (id=-1)' );
    if (addexp == true) {
        $.ajax({
            type: 'GET',
            url: wsurl,
            dataType: 'json',
            success: function(data) {
                location.reload();
            },
            error: function(data){
                alert("nok error adding experiment")
            }
        });
    }
}
*/

