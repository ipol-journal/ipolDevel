// Create a JQueryUI slider linked with a text input 
//
// inputId      the ID of the text input element
// sliderId     the ID of the DIV element to turn into a slider
// sliderMin    minimum value of the slider
// sliderMax    maximum value of the slider
// sliderStep   resolution of the slider
// numDigits    (optional) number of digits to display
function createLinkedSlider(inputId, sliderId, 
    sliderMin, sliderMax, sliderStep, numDigits)
{
    var inputObj = $(inputId);
    // Create JQueryUI slider
    var sliderObj = $(sliderId).slider({
        value: inputObj.attr('value'),  // Initial value
        min: sliderMin,                 // Minimum value
        max: sliderMax,                 // Maximum value
        step: sliderStep,               // Resolution
        animate: 'fast'});              // Animation speed    

    // If numDigits was not specified, infer from sliderStep.
    numDigits = numDigits || 
        Math.max(0, Math.ceil(-Math.log(sliderStep) / Math.log(10)));

    // Update slider when input changes
    inputObj.blur(function()
        {
            var value = inputObj.attr('value');
            var valueClamped = Math.min(Math.max(value, 
                sliderObj.slider('option', 'min')), 
                sliderObj.slider('option', 'max'));
            sliderObj.slider('value', valueClamped);

            if(value != valueClamped)
                inputObj.val(valueClamped.toFixed(numDigits));
        });

    // Update input when slider changes
    sliderObj.slider('option', 'slide',
        function(event, ui) { inputObj.val(ui.value.toFixed(numDigits)); });
}
