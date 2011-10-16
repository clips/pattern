/*### PATTERN | JAVASCRIPT:CANVAS:EDITOR ###########################################################*/
// Copyright (c) 2010 University of Antwerp, Belgium
// Authors: Tom De Smedt <tom@organisms.be>
// License: BSD (see LICENSE.txt for details).
// http://www.clips.ua.ac.be/pages/pattern

function attachEvent(element, name, f) {
    /* Cross-browser attachEvent().
     * Ensures that "this" inside the function f refers to the given element .
     */
    element[name] = Function.closure(element, f);
    if (element.addEventListener) {
        element.addEventListener(name, f, false);
    } else if (element.attachEvent) {
        element.attachEvent("on"+name, element[name]);
    } else {
        element["on"+name] = element[name];
    }
}

Function.closure = function(parent, f) {
    /* Returns the function f, where "this" inside the function refers to the given parent.
     */
    return function() { return f.apply(parent, arguments); };
}

/*##################################################################################################*/

/*--- EDITOR ---------------------------------------------------------------------------------------*/

// Since these load asynchronously, 
// use Editor in window.onload() after everything is ready:
var _path = "editor/"
document.write("<script src='" + _path + "ace/ace.js' charset='utf-8'><\/script>");
document.write("<script src='" + _path + "ace/mode-javascript.js' charset='utf-8'><\/script>");
document.write("<link rel='stylesheet' href='" + _path + "editor.css' />");

var _SYSTEM = 
    "alert|console";
var _PREDEFINED_OBJECT =
    "Array|Function|Math|document|window"
var _PREDEFINED_FUNCTION = [
    "attachEvent|getElementById|getElementsByTagName",
    "abs|acos|asin|atan|ceil|clamp|cos|degrees|exp|floor|log|max|min|pow|radians|random|round|sin|sqrt|tan|PI",
    "choice|closure|enumerate|filter|find|map|max|min|range|shuffle|sorted|sum"].join("|");
var _PREDEFINED_ATTRIBUTE = [
    "parent|element|length|width|height|frame|fps|dt|variables",
    "mouse|x|y|relative_x|relativeX|relativeY|relative_y",
    "r|g|b|a",
    "id|className|src|href|style"].join("|");
var _NODEBOX = [
    "Class",
    "geometry|angle|distance|coordinates|reflect|lerp|smoothstep",
    "lineIntersection|pointInPolygon",
    "Color|color",
    "Gradient|gradient",
    "background|fill|strokewidth|stroke|nofill|nostroke|shadow|noshadow", 
    "strokeWidth|noFill|noStroke|noShadow",
    "darker|lighter|darken|lighten|complement|analog",
    "imagesize|imageSize|image|Image",
    "fontsize|fontweight|font|lineheight",
    "fontSize|fontWeight|lineHeight",
    "textmetrics|textwidth|textheight|text",
    "textMetrics|textWidth|textHeight",
    "Point|PathElement|BezierPath", 
    "drawpath|beginpath|moveto|lineto|curveto|closepath|endpath|autoclosepath",
    "drawPath|beginPath|moveTo|lineTo|curveTo|closePath|endPath|autoClosePath",
    "beginclip|endclip",
    "beginClip|endClip", 
    "AffineTransform|Transform|Point|push|pop|translate|rotate|scale|reset",
    "line|rect|triangle|ellipse|oval|arrow|star", 
    "Mouse|Canvas|canvas|_ctx|size|print|widget|random|grid"].join("|");
var _NODEBOX_CONSTANT = [
    "RGB|HSB|HEX|LINEAR|RADIAL",
    "MOVETO|LINETO|CURVETO|CLOSE",
    "NORMAL|BOLD|ITALIC",
    "DEFAULT|HIDDEN|CROSS|HAND|POINTER|TEXT|WAIT",
    "STRING|NUMBER|BOOLEAN|RANGE|LIST|ARRAY|FUNCTION"].join("|");
var _NODEBOX_FILTER = 
    "Pixels|pixels|OffscreenBuffer|Buffer|render|blur|adjust"

function Editor(element) {
    /* Enables syntax highlighting in the given <div> element.
     */

    var punctuation = "[^a-zA-Z0-9_]|$|^";
    var mode = new (require("ace/mode/javascript").Mode)();
    var syntax = new (require("ace/mode/javascript_highlight_rules").JavaScriptHighlightRules)();
    // Syntax highlighting for function definitions: function name(arguments).
    syntax.$rules.start.splice(0, 0, {
        "token": ["keyword", "function", "text", "arguments", "text"],
        "regex": "(function )(.*?)(\\()(.*?)(\\))"
    });
    // Syntax highlighting for anonymous function: function (arguments).
    syntax.$rules.start.splice(0, 0, {
        "token": ["keyword", "text", "arguments", "text"],
        "regex": "(function)(\\()(.*?)(\\))"
    });
    // Syntax highlighting for system functions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["system", "text"],
        "regex": "("+_SYSTEM+")("+punctuation+")",
    });
    // Syntax highlighting for predefined objects.
    syntax.$rules.start.splice(0, 0, {
        "token": ["predefined_object", "text"],
        "regex": "("+_PREDEFINED_OBJECT+")("+punctuation+")",
         "next": "attribute"
    });
    // Syntax highlighting for predefined functions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["predefined_function", "text"],
        "regex": "("+_PREDEFINED_FUNCTION+")("+punctuation+")",
    });
    // Syntax highlighting for attributes.
    syntax.$rules.start.splice(0, 0, {
        "token": ["text", "predefined_attribute", "text"],
        "regex": "(\\.)("+_PREDEFINED_ATTRIBUTE+")("+punctuation+")",
         "next": "attribute"
    });
    // Syntax highlighting for NodeBox keywords.
    syntax.$rules.start.splice(0, 0, {
        "token": ["nodebox", "text"],
        "regex": "("+_NODEBOX+")([\\(|\\:|\\.])",
        "next": "attribute"
    });
    // Syntax highlighting for NodeBox commands.
    syntax.$rules.start.splice(0, 0, {
        "token": ["nodebox", "text"],
        "regex": "("+_NODEBOX_CONSTANT+")("+punctuation+")"
    });
    // Syntax highlighting for NodeBox image filters.
    syntax.$rules.start.splice(0, 0, {
        "token": ["nodebox_filter", "text"],
        "regex": "("+_NODEBOX_FILTER+")([\\(|\\:])"
    });
    // NodeBox or Python keywords followed by attributes (followed by attributes, etc.)
    syntax.$rules.attribute = [{
        "token": ["predefined_attribute", "text"],
        "regex": "("+_PREDEFINED_ATTRIBUTE+")("+punctuation+")",
         "next": "attribute"
    }, {
        "token": "empty", 
        "regex": "",
         "next": "start"
    }];
    // The "lparen" rule appears to mess up comments after "{".
    for (var i=0; i<syntax.$rules.start.length; i++) {
        if (syntax.$rules.start[i]["token"] == "lparen") {
            syntax.$rules.start[i]["next"] = null;
        }
    }
    mode.$tokenizer = new (require("ace/tokenizer").Tokenizer)(syntax.getRules());

    this._element = element;
    this._element.id = this._element.id || Math.random();
    this._element.className += " editor";
    this._ace = ace.edit(element.id);
    this._ace.setShowInvisibles(true);
    this._ace.getSession().setUseSoftTabs(false);
    this._ace.getSession().setMode(mode);
    
    this.resize = function() {
        this._ace.resize();
    };
    
    this.source = function(s) {
        /* Returns a string with the source code in the console.
         * If a string is given, sets the source code in the console.
         */
        if (s !== undefined) {
            this._ace.getSession().setValue(s);
        }
        return this._ace.getSession().getValue();
    };

};

/*--- RESIZABLE ------------------------------------------------------------------------------------*/

var UP    = "UP";
var DOWN  = "DOWN";
var LEFT  = "LEFT";
var RIGHT = "RIGHT"

function resizable(element, handle, direction, callback) {
    /* The element can be resized vertically by dragging the given handle element.
     * For example, the handle can be the bottom bar of a resizable panel.
     * The given callback function (if any) is called during resize.
     */
    var mouse = function(e) {
        if (e.touches !== undefined) {
            e.preventDefault();
            return [ // TouchEvent (iPad)
                e.touches[0].pageX, 
                e.touches[0].pageY
            ];
        } else {
            return [ // MouseEvent
                e.pageX || (e.clientX + (document.documentElement || document.body).scrollLeft), 
                e.pageY || (e.clientY + (document.documentElement || document.body).scrollTop)
            ];
        }
    }
    handle._e = element;
    handle._d = direction || DOWN;
    handle._f = callback;
    // Start drag on handle, store original element size.
    attachEvent(handle, "mousedown", function(e) {
        window._drag = this;
        this._o = mouse(e);
        this._w = this._e.offsetWidth;
        this._h = this._e.offsetHeight;
    });
    // Resize element by adding drag offset to original size.
    attachEvent(window, "mousemove", function(e) {
        if (window._drag) {
            var d = window._drag;
            var m = mouse(e);
            var i = (d._d == UP || d._d == LEFT)? -1 : 1;
            if (d._d == UP || d._d == DOWN) {
                d._e.style.height = d._h + i * (m[1] - d._o[1]) + "px";
            } else if (d._d == LEFT || d._d == RIGHT) {
                d._e.style.width = d._w + i * (m[0] - d._o[0]) + "px";
            }
            d._f && d._f(d._e);
        }
    });
    // Stop drag.
    attachEvent(window, "mouseup", function(e) {
        window._drag = null;
    });
}
