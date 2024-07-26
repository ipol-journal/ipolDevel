let csrftoken = getCookie('csrftoken');


$(document).ready(function(){
    $('#show').click(function (event) {
        showModal();
    });
});

function displayWarning(){
    let selectDemoState = document.getElementById('SelectDemoState');
    let testDemoStateSelect = document.getElementById('TestDemoStateSelect');
    if (selectDemoState.value == "Test"){
        testDemoStateSelect.innerHTML = 'WARNING: Test demo is only for testing and will be removed in 6 months. Use workshop state to keep the unpublished demo';
    } else {
        testDemoStateSelect.innerHTML = '';
    }
    return;
}

function showModal(){
   var id = '#modal';
   $(id).html(`
        <h1>Create new demo</h1>
        <form id="DemoForm" action="addDemo/ajax" autocomplete="off" method="post" enctype="multipart/form-data">
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrftoken}">
            <div id="newDemo-formFields">
                <label for="newDemoID">Demo ID: </label>
                <input type="number" id="newDemoID" name="demo_id" required>
                <label for="newDemoTitle">Title: </label>
                <input type="text" id="newDemoTitle" name="title" required>
                <label for="SelectDemoState">State: </label>
                <select form="DemoForm" id="SelectDemoState" name="state" onclick="displayWarning()">
                    <option>Preprint</option>
                    <option>Published</option>
                    <option>Test</option>
                    <option>Example</option>
                    <option>Workshop</option>
                </select>
            </div>
            <p id="TestDemoStateSelect" style="color:red;"></p>
            <div id="newDemo-buttons">
                <button id="ButtonAddDemo" type="submit">Create</button>
                <button class="close">Cancel</button>
            </div>
        </form>
    `);

    $('#fond').fadeIn(500)   
    $('#fond').fadeTo("slow",0.7);
    $(id).fadeIn(300);

    $('.popup .close').click(function (event) {
        event.preventDefault();
        hideModal();
    });
}

function hideModal(){
   $('#fond, .popup').hide();
   $('.popup').html('');
}
