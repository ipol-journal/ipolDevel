/**
 * @file 
 * this file contains the code related to drawing features base class
 * @author  Karl Krissian
 * @version 0.1
 */

"use strict";

// ipol application namespace
var ipol = ipol || {};

/**
 * features namespace for additional interface 
 * required by some demos like drawing, display of specific inputs, etc ...
 * @namespace
 */
ipol.features = ipol.features || {};


//------------------------------------------------------------------------------
/**
 * Base class for additional drawing features
 * @constructor
 */
ipol.features.DrawBase = function() {
}


//------------------------------------------------------------------------------
/**
 * Creates and returns the HTML code for the drawing interface
 * @function createHTML
 * @memberOf ipol.features.DrawBase.prototype
 * @returns {string} the HTML code
 */
ipol.features.DrawBase.prototype.createHTML = function( ) {
    return "";
}

//------------------------------------------------------------------------------
/**
 * Create the events for the drawing interface
 * @function createHTMLEvents
 * @memberOf ipol.features.DrawBase.prototype
 * @returns {string} the HTML code
 */
ipol.features.DrawBase.prototype.createHTMLEvents = function( ) {
}

//------------------------------------------------------------------------------
/**
 * Updates the drawing interface
 * @function updateDrawing
 * @memberOf ipol.features.DrawBase.prototype
 */
ipol.features.DrawBase.prototype.updateDrawing = function() {
}

//------------------------------------------------------------------------------
/**
 * Add created elements as a property in the parameters object
 * @function AddToParameters
 * @memberOf ipol.features.DrawBase.prototype
 * @param params object containing the parameters
 */
ipol.features.DrawBase.prototype.AddToParameters = function(params) {
}

//------------------------------------------------------------------------------
/**
 * Submit data to the form data for uploading and call upload_callback
 * or does nothing and return false
 * @function submitDrawing
 * @return {boolean} if a feature has been submitted
 * @memberOf ipol.features.DrawBase.prototype
 */
ipol.features.DrawBase.prototype.submitDrawing = function(ddl_json, formData, upload_callback) {
    return false;
}


//------------------------------------------------------------------------------
/**
 * Gets the current drawing interface state: different options like pen size
 * color and current actions (drawn lines)
 * @function getState
 * @memberOf ipol.features.DrawBase.prototype
 */
ipol.features.DrawBase.prototype.getState = function() {
    return {};
}


//------------------------------------------------------------------------------
/**
 * Sets the current drawing interface state: different options like pen size
 * color and current actions (drawn lines)
 * @function setState
 * @memberOf ipol.features.DrawBase.prototype
 */
ipol.features.DrawBase.prototype.setState = function( state) {
}
