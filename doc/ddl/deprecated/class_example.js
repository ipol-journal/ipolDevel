// we use strict mode for better compatibility
"use strict";

// ipol application namespace
var ipol = ipol || {};

// class definition
ipol.ClassExample = function()  {

    // we declare member variable
    // the private member _this will be available to private methods
    var _this = this;
    var _private_var;
    
    this.public_var = value;

    // we declare private methods
    var _privateMethod1 = function() {
    }
    var _privateMethod2 = function() {
        // can use private variables and methods directly
        _private_var = value;
        _privateMethod1();
        // it can use public var or methods through "_this"
        // because it has its own local object this
        _this.public_var = value;
        _this.publicMethod1();
    };
    
    // we declare public methods
    this.publicMethod1 = function() {
    }
    this.publicMethod2 = function() {
        // can use private variables and methods directly
        _private_var = value;
        _privateMethod1();
        // it can use public var or methods through "this"
        // since publicMethod is a function of the object "this"
        this.public_var = value;
        this.publicMethod1();
    };
    
    // if called with "new", will return "this" object so 
    // elements in "this" are available in the class instance
}

// static member
ipol.ClassExample.staticExample = function() {
    ...
}

// instance of ClassExample, with access to public members
ipol.object = new ipol.ClassExample();

