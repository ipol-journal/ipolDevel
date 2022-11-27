    //-----------------------------------------Status Module-----------------------------------------//

    function estate(jsonObj, idDiv, moduleName) {
        var status = jsonObj['status'];
        if (status === "OK") {
            $('#' + idDiv).prepend(`<h2>${moduleName} module is running: <i class="fa-solid fa-check"></i></i></h2>`);
        } else {
            $('#' + idDiv).prepend(`<h2>' ${moduleName} does not respond!  <i class="fa-solid fa-triangle-exclamation"></i></h2>`);
        }
    }
    //-----------------------------------------Request AJAX---------------------------------//   
    //-----------------------------------------DR-----------------------------------------//
    function chargeDR(data) {
        for (const dr of data.demorunners) {
            let DRStatus = '<i class="fa-solid fa-triangle-exclamation">';
            let workload = dr.workload
            if (dr.status == 'OK') {
                DRStatus = '<i class="fa-solid fa-check">';
            } else {
                workload = 'N/A'
            }
            $('#dr-table').append(`
                <tr>
                    <td>${dr.name}</td>
                    <td>${workload}</td>
                    <td>${DRStatus}</td>
                </tr>
            `)
        }
    };

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/dispatcher/get_demorunners_stats',
            success: function(data) {
                $('#DR').prepend(`<h2>Demorunner module:</i></h2>`);
                chargeDR(data);
            },
            error: function() {
                $('#DR').html('<h2>Could not obtain the list of demoRunners!  <i class="fa-solid fa-triangle-exclamation"></i></h2>')
            }
        });
        return false;
    });

    //-----------------------------------------Archive-----------------------------------------//

    function chargeArchive(data) {
        $('#Archive').append('<p>Number of blobs: ' + data.nb_blobs + '</p>');
        $('#Archive').append('<p>Number of experiments: ' + data.nb_experiments + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/archive/stats',
            success: function(data) {
                estate(data, "Archive", "Archive");
                chargeArchive(data);
            },
            error: function() {
                $('#Archive').html('<h2>Archive does not respond! <i class="fa-solid fa-triangle-exclamation"></i></h2>')
            }
        });
        return false;
    });

    //-----------------------------------------DI-----------------------------------------//

    function chargeDI(data) {
        $('#DI').append('<p>Number of demos: ' + data.nb_demos + '</p>');
        $('#DI').append('<p>Number of authors: ' + data.nb_authors + '</p>');
        $('#DI').append('<p>Number of editors: ' + data.nb_editors + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/demoinfo/stats',
            success: function(data) {
                estate(data, "DI", "DemoInfo");
                chargeDI(data);
            },
            error: function() {
                $('#DI').html('<h2>DemoInfo does not respond! <i class="fa-solid fa-triangle-exclamation"></i></h2>')
            }
        });
        return false;
    });

    //-----------------------------------------Blobs-----------------------------------------//

    function chargeBlobs(data) {
        $('#Blobs').append('<p>Number of blobs: ' + data.nb_blobs + '</p>');
        $('#Blobs').append('<p>Number of templates: ' + data.nb_templates + '</p>');
    }

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/blobs/stats',
            success: function(data) {
                estate(data, "Blobs", "Blobs");
                chargeBlobs(data);
            },
            error: function() {
                $('#Blobs').html('<h2>Blobs does not respond! <i class="fa-solid fa-triangle-exclamation"></i></h2>')
            }
        });
        return false;
    });

    //-----------------------------------------Core-----------------------------------------//

    $(function() {
        $.ajax({
            type: 'GET',
            dataType: 'json',
            url: '/api/core/ping',
            success: function(data) {
                estate(data, "Core", "Core");
            },
            error: function() {
                $('#Core').html('<h2>Core does not respond! <i class="fa-solid fa-triangle-exclamation"></i></h2>')
            }
        });
        return false;
    });
