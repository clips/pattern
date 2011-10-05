/*### PATTERN | JAVASCRIPT:CANVAS:EDITOR ###########################################################*/
// Copyright (c) 2010 University of Antwerp, Belgium
// Authors: Tom De Smedt <tom@organisms.be>
// License: BSD (see LICENSE.txt for details).
// http://www.clips.ua.ac.be/pages/pattern

function attachEvent(element, name, f) {
    /* Cross-browser attachEvent().
     * Ensures that "this" inside the function f refers to the given element .
     */
    element[name] = function() { return f.apply(parent, arguments); }
    if (element.addEventListener) {
        element.addEventListener(name, f, false);
    } else if (element.attachEvent) {
        element.attachEvent("on"+name, element[name]);
    } else {
        element["on"+name] = element[name];
    }
}

/*##################################################################################################*/

/*--- EDITOR ---------------------------------------------------------------------------------------*/

// Since these load asynchronously, 
// only use Editor in window.onload() when everything is ready:
var _path = "editor/"
document.write("<script src='"+_path+"ace/ace.js' charset='utf-8'><\/script>");
document.write("<script src='"+_path+"ace/mode-javascript.js' charset='utf-8'><\/script>");
document.write("<link rel='stylesheet' href='"+_path+"editor.css' />");

var _SYSTEM = 
    "window|alert|console";
var _MATH =
    "abs|acos|asin|atan|ceil|cos|degrees|exp|floor|log|max|min|pow|radians|random|round|sin|sqrt|tan|PI";
var _ARRAY =
    "choice|enumerate|filter|find|map|range|shuffle|sorted|sum";
var _ATTRIBUTE = [
    "parent|element|width|height|frame|fps|dt|variables",
    "mouse|x|y|relative_x|relativeX|relativeY|relative_y",
    "r|g|b|a",
    "id|className|src|href|style"].join("|");
var _NODEBOX = [
    "__Class__",
    "geometry|angle|distance|coordinates|reflect|lerp|smoothstep",
    "lineIntersection|pointInPolygon",
    "Color|color",
    "Gradient|gradient",
    "background|fill|strokewidth|stroke|nofill|nostroke|shadow|noshadow", 
    "strokeWidth|noFill|noStroke|noShadow",
    "darker|lighter|darken|lighten|complement|analog",
    "imagesize|imageSize|image|Image|Pixels|pixels",
    "fontsize|fontweight|font|lineheight",
    "fontSize|fontWeight|lineHeight",
    "textmetrics|textwidth|textheight|text",
    "textMetrics|textWidth|textHeight",
    "PathElement|BezierPath", 
    "drawpath|beginpath|moveto|lineto|curveto|closepath|endpath|autoclosepath",
    "drawPath|beginPath|moveTo|lineTo|curveTo|closePath|endPath|autoClosePath",
    "beginclip|endclip",
    "beginClip|endClip", 
    "AffineTransform|Transform|Point|push|pop|translate|rotate|scale|reset",
    "line|rect|triangle|ellipse|oval|arrow|star", 
    "Mouse|Canvas|canvas|_ctx|size|print|widget|random|grid"].join("|");
var _NODEBOX_CONSTANT = [
    "RGB|HSB|LINEAR|RADIAL",
    "MOVETO|LINETO|CURVETO|CLOSE",
    "NORMAL|BOLD|ITALIC",
    "DEFAULT|HIDDEN|CROSS|HAND|POINTER|TEXT|WAIT",
    "STRING|NUMBER|BOOLEAN|RANGE|LIST|ARRAY|FUNCTION"].join("|");
var _NODEBOX_FILTER = 
    "OffscreenBuffer|Buffer|render|blur"

function Editor(element) {
    /* Enables syntax highlighting in the given <div> element.
     */

    var punctuation = "[^a-zA-Z0-9_]|$";
    var mode = new (require("ace/mode/javascript").Mode)();
    var syntax = new (require("ace/mode/javascript_highlight_rules").JavaScriptHighlightRules)();
    // Syntax highlighting for function definitions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["keyword", "function", "text", "arguments", "text"],
        "regex": "(function )(.*?)(\\()(.*?)(\\))"
    });
    // Syntax highlighting for system functions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["system", "text"],
        "regex": "("+_SYSTEM+")("+punctuation+")",
    });
    // Syntax highlighting for Math functions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["Math", "text", "math"],
        "regex": "(Math)(\\.)("+_MATH+")"
    });
    // Syntax highlighting for Array functions.
    syntax.$rules.start.splice(0, 0, {
        "token": ["Array", "text", "array"],
        "regex": "(Array)(\\.)("+_ARRAY+")"
    });
    // Syntax highlighting for attributes.
    syntax.$rules.start.splice(0, 0, {
        "token": ["text", "attribute", "text"],
        "regex": "(\\.)("+_ATTRIBUTE+")("+punctuation+")",
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
        "token": ["filter", "text"],
        "regex": "("+_NODEBOX_FILTER+")([\\(|\\:])"
    });
    // NodeBox or Python keywords followed by attributes (followed by attributes, etc.)
    syntax.$rules.attribute = [{
        "token": ["attribute", "text"],
        "regex": "("+_ATTRIBUTE+")("+punctuation+")",
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
    
    this.source = function() {
        /* Returns a string with the source code in the console.
         */
        return this._ace.getSession().getValue();
    };
    
    this.resize = function() {
        this._ace.resize();
    }
};

/*--- RESIZABLE ------------------------------------------------------------------------------------*/

var UP    = "up";
var DOWN  = "down";
var LEFT  = "left";
var RIGHT = "right";

function resizable(element, handle, callback) {
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
            //d._e.style.width = d._w - m[0] + d._o[0] + "px";
            d._e.style.height = d._h - m[1] + d._o[1] + "px";
            d._f && d._f(d._e);
        }
    });
    // Stop drag.
    attachEvent(window, "mouseup", function(e) {
        window._drag = null;
    });
}
