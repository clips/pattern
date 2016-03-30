/*### PATTERN | CANVAS.JS ###########################################################################*/
// Copyright (c) 2010 University of Antwerp, Belgium
// Authors: Tom De Smedt <tom@organisms.be>
// License: BSD (see LICENSE.txt for details).
// Version: 1.4
// http://www.clips.ua.ac.be/pages/pattern-canvas

// The NodeBox drawing API for the HTML5 <canvas> element.
// The commands are adopted from NodeBox for OpenGL (http://www.cityinabottle.org/nodebox),
// including a (partial) port from nodebox.graphic.bezier, 
// nodebox.graphics.geometry and nodebox.graphics.shader.

/*##################################################################################################*/

try { $; } catch(e) {
    function $(x, y) {
        return Array.copy(((y !== undefined)? y : document).querySelectorAll(x));
    }
}

function attachEvent(element, name, f) {
    /* Cross-browser attachEvent().
     * Ensures that "this" inside the function f refers to the given element .
     */
    f = Function.closure(element, f);
    if (element.addEventListener) {
        element.addEventListener(name, f, false);
    } else if (element.attachEvent) {
        element.attachEvent("on"+name, f);
    } else {
        element["on"+name] = f;
    }
    element[name] = f; // So we can do element.name(), see widget().
}

Function.closure = function(parent, f) {
    /* Returns the function f, where "this" inside the function refers to the given parent.
     */
    return function() { return f.apply(parent, arguments); };
};

window.width = function() {
    return (window.innerWidth !== undefined)? window.innerWidth : document.documentElement.clientWidth;
};
window.height = function() {
    return (window.innerHeight !== undefined)? window.innerHeight : document.documentElement.clientHeight;
};

/*##################################################################################################*/

/*--- ARRAY FUNCTIONS ------------------------------------------------------------------------------*/

// JavaScript Array object:
// var a = [1,2,3];
// 1 in [1,2,3] => true;
// [1,2,3].indexOf(1) => 0
// [1,2,3].push(4) => [1,2,3,4]
// [1,2,3].pop() => [1,2] 3
// [1,2,3].shift() => 1 [2,3]
// [1,2,3].concat([4,5,6]) => [1,2,3,4,5,6] copy
// [1,2,3].slice(1,2) => [2,3]
// [1,2,3].splice(1,0,11,12) => [1,11,12,2,3]
// [1,2,3].splice(1,2) => [1]
// [1,2,3].join(",") => "1,2,3"

// Additional array functions are invoked with Array.[function].

Array.instanceof = function(array) {
    return Object.prototype.toString.call(Array) === "[object Array]";
};

Array.get = function(array, index) {
    return (index >= 0)? array[index] : array[array.length+index];
}

Array.index = function(array, v) {
    for (var i=0; i < array.length; i++) { if (array[i] === v) return i; }
    return -1;
};

Array.contains = function(array, v) {
    for (var i=0; i < array.length; i++) { if (array[i] === v) return true; }
    return false;
};

Array.find = function(array, match) {
    for (var i=0; i < array.length; i++) { if (match(array[i])) return i; }
};

Array.sum = function(array) {
    for (var i=0, sum=0; i < array.length; sum+=array[i++]){}; return sum;
};

Array.min = function(array, callback) {
    callback = callback || function(x) { return x; }
    var x = +Infinity;
    for (var i=0; i < array.length; i++) { 
        x = Math.min(x, callback(array[i])); 
    }
    return x;
};

Array.max = function(array, callback) {
    callback = callback || function(x) { return x; }
    var x = -Infinity;
    for (var i=0; i < array.length; i++) { 
        x = Math.max(x, callback(array[i])); 
    }
    return x;
};

Array.map = function(array, callback) {
    /* Returns a new array with callback(value) for each value in the given array.
     */
    var a = []; 
    for (var i=0; i < array.length; i++) { 
        a.push(callback(array[i])); 
    } 
    return a;
};

Array.filter = function(array, callback) {
    /* Returns a new array with values for which callback(value)==true.
     */
    var a = []; 
    for (var i=0; i < array.length; i++) { 
        if (callback(array[i])) a.push(array[i]); 
    } 
    return a;
};

Array.enumerate = function(array, callback, that) {
    /* Calls callback(index, value) for each value in the given array.
     */
    callback = Function.closure(that || this, callback);
    for (var i=0; i < array.length; i++) {
        if (callback(i, array[i]) == false) return;
    }
};

Array.forEach = function(array, callback, that) {
    /* Calls callback(value, index, array) for each value in the given array.
     */
    callback = Function.closure(that || this, callback);
    for (var i=0; i < array.length; i++) {
        if (callback(array[i]) == false, i, array) return;
    }
}

Array.eq = function(array1, array2) {
    /* Returns true if both arrays contain the same values.
     */
    if (!(array1 instanceof Array) || 
        !(array2 instanceof Array) ||  array1.length != array2.length) {
        return false;
    }
	for (var i=0; i < array1.length; i++) {
		if (array1[i] !== array2[i]) return false;
	}
	return true;
};

Array.sorted = function(array, reverse, key) {
    /* Returns a sorted copy of the given array.
     */
    if (key instanceof Function) {
        var cmp = function(a, b) { return key(b) - key(a); }
    } else {
        var cmp = undefined
    }
    array = array.slice();
    array = array.sort(cmp);
    if (reverse) array = array.reverse();
    return array;
};

Array.reversed = function(array) {
    /* Returns a reversed copy of the given array.
     */
    array = array.slice();
    array = array.reverse();
    return array;
};

Array.unique = function (array) {
    /* Returns a new array with unique items.
     */
    var a = array.slice();
    for (var i=a.length-1; i > 0; --i) {
        var v = a[i];
        for (var j=i-1; j >= 0; --j) {
            if (a[j] === v) a.splice(j, 1); i--;
        }
    }
    return a;
};

Array.copy = function(array) {
    /* Returns a shallow copy of the given array.
     */
    var a = [];
    for (var i=0; i < array.length; i++) {
        a.push(array[i]);
    }
    return a;
};

Array.choice = function(array) {
    /* Returns a random value from the given array (undefined if empty).
     */
    return array[Math.round(Math.random() * (array.length-1))];
};

Array.shuffle = function(array) {
    /* Randomly shuffles the values in the given array.
     */
    var n = array.length;
    var i = n;
    while (i--) {
        var p = parseInt(Math.random() * n);
        var x = array[i];
        array[i] = array[p];
        array[p] = x;
    }
    return array;
};

Array.shuffled = function(array) {
	/* Returns a new array with randomly shuffled values.
	 */
	return Array.shuffle(array.slice());
};

Array.range = function(i, j) {
    /* Returns a new array with numeric values from i to j (not including j).
     */
    if (j === undefined) { 
        j = i; 
        i = 0; 
    }
    var a = [];
    for (var k=0; k<j-i; k++) {
        a[k] = i + k;
    }
    return a;
};

Array.len = function(array) {
	/* Returns the length of the given array.
	 */
    return array.length;
};

// Since version 1.5:

var sum       = Array.sum;
var map       = Array.map;
var filter    = Array.filter;
var enumerate = Array.enumerate;
var sorted    = Array.sorted;
var reversed  = Array.reversed;
var unique    = Array.unique;
var shuffled  = Array.shuffled;
var choice    = Array.choice;
var range     = Array.range;
var len       = Array.len;

/*--- ARRAY EXTENSIONS -----------------------------------------------------------------------------*/

if (Array.isArray === undefined) {
	Array.isArray = Array.instanceof;
}

if (!Array.prototype.get) {
	 Array.prototype.get = function(i) {
		return Array.get(this, i);
	 }
}

if (!Array.prototype.index) {
	 Array.prototype.index = function(v) {
		return Array.index(this, v);
	 };
}

if (!Array.prototype.contains) {
	 Array.prototype.contains = function(v) {
		return Array.contains(this, v);
	};
}

if (!Array.prototype.find) {
	 Array.prototype.find = function(match) {
		return Array.find(this, match);
	 };
}

if (!Array.prototype.min) {
	 Array.prototype.min = function(callback) {
		return Array.min(this, callback);
	 };
}

if (!Array.prototype.max) {
	 Array.prototype.max = function(callback) {
		return Array.max(this, callback);
	 };
}

if (!Array.prototype.map) {
	 Array.prototype.map = function(callback) {
		return Array.map(this, callback);
	 };
}

if (!Array.prototype.filter) {
	 Array.prototype.filter = function(callback) {
		return Array.filter(this, callback);
	 };
}

if (!Array.prototype.forEach) {
	 Array.prototype.forEach = function(callback, that) {
		return Array.forEach(this, callback, that);
	 };
}

if (!Array.prototype.eq) {
	 Array.prototype.eq = function(array) {
		return Array.eq(this, array);
	 };
}

if (!Array.prototype.shuffle) {
	 Array.prototype.shuffle = function() {
		return Array.shuffle(this);
	 };
}

/*##################################################################################################*/

/*--- BASE CLASS -----------------------------------------------------------------------------------*/
// JavaScript class inheritance, John Resig, 2008 (http://ejohn.org/blog/simple-javascript-inheritance).
//
// var Person = Class.extend({
//     init: function(name) {
//         this.name = name;
//     }
// });
//
// var Employee = Person.extend({
//     init: function(name, salary) {
//         this._super(name); // Call Person.init().
//         this.salary = salary;
//     }
// });
//
// var e = new Employee("tom", 10);

(function() {
    var initialized = false;
    var has_super = /xyz/.test(function() { xyz; }) ? /\b_super\b/ : /.*/;
    this.Class = function(){};
    Class.extend = function(properties) {
        // Instantiate base class (create the instance, don't run the init constructor).
        var _super = this.prototype;
        initialized = true; var p = new this(); 
        initialized = false;
        // Copy the properties onto the new prototype.
        for (var k in properties) {
            p[k] = typeof properties[k] == "function" 
                && typeof _super[k] == "function" 
                && has_super.test(properties[k]) ? (function(k, f) { return function() {
                    // If properties[k] is actually a method,
                    // add a _super() method (= same method but on the superclass).
                    var s, r;
                    s = this._super; 
                    this._super = _super[k]; r = f.apply(this, arguments); 
                    this._super = s;
                    return r;
                }; 
            })(k, properties[k]) : properties[k];
        }
        function Class() {
            if (!initialized && this.init) {
                this.init.apply(this, arguments);
            }
        }
        Class.constructor = Class;
        Class.prototype = p;
        // Make the class extendable.
        Class.extend = arguments.callee;
        return Class;
    };
})();

/*##################################################################################################*/

/*--- MATH -----------------------------------------------------------------------------------------*/

var PI = Math.PI;

Math.degrees = function(radians) {
    return radians * 180 / Math.PI;
};

Math.radians = function(degrees) {
    return degrees / 180 * Math.PI;
};

Math._round = Math.round;
Math.round = function(x, decimals) {
    if (!decimals) {
        return Math._round(x);
    } else {
        return Math._round(x * Math.pow(10, decimals)) / Math.pow(10, decimals);
    }
};

Math.mod = function(a, b) {
    return ((a % b) + b) % b;
};

Math.sign = function(x) {
    if (x < 0) return -1;
    if (x > 0) return +1;
    return 0;
}

Math.clamp = function(value, min, max) {
    if (max > min) {
        return Math.max(min, Math.min(value, max));
    } else {
        return Math.max(max, Math.min(value, min));
    }
};

Math.normalize = function(value, min, max) {
    return (value - min) / (max - min);
}

Math.sum = function(a) {
    var n = 0;
    for (var i=0; i < a.length; i++) n += a[i];
    return n;
};

Math.dot = function(a, b) {
    var m = Math.min(a.length, b.length);
    var n = 0;
    for (var i = 0; i < m; i++) n += a[i] * b[i];
    return n;
};

Math.mix = function(a, b, t) {
    if (t < 0.0) return a;
    if (t > 1.0) return b;
    return a + (b-a)*t;
};

Math.lerp = Math.mix;

Math.smoothstep = function(a, b, x) {
    if (x < a) return 0.0;
    if (x >=b) return 1.0;
    x = (x-a) / (b-a);
    return x*x * (3-2*x);
};

Math.smoothrange = function(a, b, n) {
    /* Returns an array of approximately n values v1, v2, ... vn,
     * so that v1 <= a, and vn >= b, and all values are multiples of 1, 2, 5 and 10.
     * For example: Math.smoothrange(1, 123) => [0, 20, 40, 60, 80, 100, 120, 140],
     */
    function _multiple(v, round) {
        var e = Math.floor(Math.log(v) / Math.LN10); // exponent
        var m = Math.pow(10, e);                     // magnitude
        var f = v / m;                               // fraction
        if (round) {
            if (f <  1.5) return m * 1;
            if (f <  3.0) return m * 2;
            if (f <  7.0) return m * 5;
        } else {
            if (f <= 1.0) return m * 1;
            if (f <= 2.0) return m * 2;
            if (f <= 5.0) return m * 5; 
        }
        return m * 10;
    }
    if (a === undefined && b === undefined) { a=0; b=1; }
    if (a === undefined) { a=0; b=b; }
    if (b === undefined) { a=0; b=a; }
    if (n === undefined) { n=10; }
    if (a === b) {
        return [a];
    }
    var r = _multiple(b-a);
    var t = _multiple(r / (n-1), true);
    a = Math.floor(a/t) * t;
    b = Math.ceil( b/t) * t;
    var rng = [];
    for (var i=0; i < (b-a) / t + 1; i++) {
        rng.push(a + i*t);
    }
    return rng;
};

/*--- GEOMETRY -------------------------------------------------------------------------------------*/

var Point = Class.extend({
    init: function(x, y) {
        this.x = x;
        this.y = y;        
    },
    copy: function() {
        return new Point(this.x, this.y);
    }
});

var Geometry = Class.extend({

    // ROTATION:
    
    angle: function(x0, y0, x1, y1) {
        /* Returns the angle between two points.
         */
        return Math.degrees(Math.atan2(y1-y0, x1-x0));
    },
    
    distance: function(x0, y0, x1, y1) {
        /* Returns the distance between two points.
         */
        return Math.sqrt(Math.pow(x1-x0, 2) + Math.pow(y1-y0, 2));
    },
    
    coordinates: function(x0, y0, distance, angle) {
        /* Returns the location of a point by rotating around origin (x0,y0).
         */
        var x1 = x0 + Math.cos(Math.radians(angle)) * distance;
        var y1 = y0 + Math.sin(Math.radians(angle)) * distance;
        return new Point(x1, y1);
    },

    rotate: function(x, y, x0, y0, angle) {
        /* Returns the coordinates of (x,y) rotated clockwise around origin (x0,y0).
         */
        x -= x0;
        y -= y0;
        var a = Math.cos(Math.radians(angle));
        var b = Math.sin(Math.radians(angle));
        return new Point(
            x*a - y*b + x0, 
            y*a + x*b + y0
        );
    },

    reflect: function(x0, y0, x1, y1, d, a) {
        // Returns the reflection of a point through origin (x0,y0).
        if (d === undefined ) d = 1.0;
        if (a === undefined) a = 180;
        d *= this.distance(x0, y0, x1, y1);
        a += this.angle(x0, y0, x1, y1);
        return this.coordinates(x0, y0, d, a);
    },

    // INTERPOLATION:

    lerp: function(a, b, t) {
        /* Returns the linear interpolation between a and b for time t between 0.0-1.0.
         * For example: lerp(100, 200, 0.5) => 150.
         */
        if (t < 0.0) return a;
        if (t > 1.0) return b;
        return a + (b-a)*t;
    },
    
    smoothstep: function(a, b, x) {
        /* Returns a smooth transition between 0.0 and 1.0 using Hermite interpolation (cubic spline),
         * where x is a number between a and b. The return value will ease (slow down) as x nears a or b.
         * For x smaller than a, returns 0.0. For x bigger than b, returns 1.0.
         */
        if (x < a) return 0.0;
        if (x >=b) return 1.0;
        x = (x-a) / (b-a);
        return x*x * (3-2*x);
    },
    
    bounce: function(x) {
        /* Returns a bouncing value between 0.0 and 1.0 (e.g. Mac OS X Dock) for a value between 0.0-1.0.
         */
        return Math.abs(Math.sin(2 * Math.PI * (x+1) * (x+1)) * (1-x));
    },
    
    // ELLIPSES:
    
    superformula: function(m, n1, n2, n3, phi) {
        /* A generalization of the superellipse (Gielis, 2003).
         * that can be used to describe many complex shapes and curves found in nature.
         */
        if (n1 == 0) return (0, 0);
        var a = 1.0;
        var b = 1.0;
        var r = Math.pow(Math.pow(Math.abs(Math.cos(m * phi/4) / a), n2) +
                         Math.pow(Math.abs(Math.sin(m * phi/4) / b), n3), 1/n1);
        if (Math.abs(r) == 0)
            return (0, 0);
        r = 1 / r;
        return [r * Math.cos(phi), r * Math.sin(phi)];
    },
    
    // INTERSECTION:

    lineIntersection: function(x1, y1, x2, y2, x3, y3, x4, y4, infinite) {
        /* Determines the intersection point of two lines, or two finite line segments if infinite=False.
         * When the lines do not intersect, returns null.
         */
        // Based on: P. Bourke, 1989, http://paulbourke.net/geometry/pointlineplane/
        if (infinite === undefined) infinite = false;
        var ua = (x4-x3) * (y1-y3) - (y4-y3) * (x1-x3);
        var ub = (x2-x1) * (y1-y3) - (y2-y1) * (x1-x3);
        var d  = (y4-y3) * (x2-x1) - (x4-x3) * (y2-y1);
        // The lines are coincident if (ua == ub && ub == 0).
        // The lines are parallel otherwise.
        if (d == 0) return null;
        ua /= d;
        ub /= d;
        // Intersection point is within both finite line segments?
        if (!infinite && !(0 <= ua && ua <= 1 && 0 <= ub && ub <= 1)) return null;
        return new Point(
            x1 + ua * (x2-x1),
            y1 + ua * (y2-y1)
        );
    },

    pointInPolygon: function(points, x, y) {
        /* Ray casting algorithm.
         * Determines how many times a horizontal ray starting from the point 
         * intersects with the sides of the polygon. 
         * If it is an even number of times, the point is outside, if odd, inside.
         * The algorithm does not always report correctly when the point is very close to the boundary.
         * The polygon is passed as an array of Points.
         */
        // Based on: W. Randolph Franklin, 1970, http://www.ecse.rpi.edu/Homepages/wrf/Research/Short_Notes/pnpoly.html
        var odd = false;
        var n = points.length;
        for (var i=0; i < n; i++) {
            var j = (i<n-1)? i+1 : 0;
            var x0 = points[i].x;
            var y0 = points[i].y;
            var x1 = points[j].x;
            var y1 = points[j].y;
            if ((y0 < y && y1 >= y) || (y1 < y && y0 >= y)) {
                if (x0 + (y-y0) / (y1-y0) * (x1-x0) < x) {
                    odd = !odd;
                }
            }
        }
        return odd;
    },
    
    Bounds: Class.extend({
        init: function(x, y, width, height) {
            /* Creates a bounding box.
             * The bounding box is an untransformed rectangle that encompasses a shape or group of shapes.
             */
            if (width === undefined) width = Infinity;
            if (height === undefined) height = Infinity;
            // Normalize if width or height is negative:
            if (width < 0) {
                 x+=width; width=-width;
            }
            if (height < 0) {
                y+=height; height=-height;
            }
            this.x = x;
            this.y = y;
            this.width = width ;
            this.height = height;
        },
        
        copy: function() {
            return new Bounds(this.x, this.y, this.width, this.height);
        },
        
        intersects: function(b) {
            /* Return True if a part of the two bounds overlaps.
             */
            return Math.max(this.x, b.x) < Math.min(this.x + this.width, b.x + b.width)
                && Math.max(this.y, b.y) < Math.min(this.y + this.height, b.y + b.height);
        },
        
        intersection: function(b) {
            /* Returns bounds that encompass the intersection of the two.
             * If there is no overlap between the two, null is returned.
             */
            if (!this.intersects(b)) {
                return null;
            }
            var mx = Math.max(this.x, b.x);
            var my = Math.max(this.y, b.y);
            return new Bounds(mx, my, 
                Math.min(this.x + this.width, b.x+b.width) - mx, 
                Math.min(this.y + this.height, b.y+b.height) - my
            );
        },

        union: function(b) {
            /* Returns bounds that encompass the union of the two.
             */
            var mx = Math.min(this.x, b.x);
            var my = Math.min(this.y, b.y);
            return new Bounds(mx, my, 
                Math.max(this.x + this.width, b.x+b.width) - mx, 
                Math.max(this.y + this.height, b.y+b.height) - my
            );
        },
        
        contains: function(pt) {
            /* Returns True if the given point or rectangle falls within the bounds.
             */
            if (pt instanceof Point) {
                return pt.x >= this.x && pt.x <= this.x + this.width
                    && pt.y >= this.y && pt.y <= this.y + this.height                
            }
            if (pt instanceof Bounds) {
                return pt.x >= this.x && pt.x + pt.width <= this.x + this.width
                    && pt.y >= this.y && pt.y + pt.height <= this.y + this.height
            }
            
        }
    })
});

var geometry = new Geometry();
var geo = geometry;

Math.angle = geometry.angle;
Math.distance = geometry.distance;
Math.coordinates = geometry.coordinates;

/*##################################################################################################*/

/*--- COLOR ----------------------------------------------------------------------------------------*/

var RGB = "RGB";
var HSB = "HSB";
var HCL = "HCL";
var HEX = "HEX";

var Color = Class.extend({

//  init: function(r, g, b, a, {base: 1.0, colorspace: RGB})
    init: function(r, g, b, a, options) {
        /* A color with R,G,B,A channels, with channel values ranging between 0.0-1.0.
         * Either takes four parameters (R,G,B,A), three parameters (R,G,B),
         * two parameters (grayscale and alpha) or one parameter (grayscale or Color object).
         * An optional {base: 1.0, colorspace: RGB} can be used with four parameters.
         */
        var base = options && options.base || 1.0;
        var colorspace = options && options.colorspace || RGB;
        // One value, a hexadecimal string.
		if (r && r.match && r.match(/^#/)) {
			colorspace = HEX;
		// One value, another color object.
		} else if (r instanceof Color) {
            g=r.g; b=r.b; a=r.a; r=r.r;
        // One value, array with R,G,B,A values.
        } else if (r instanceof Array) {
            g=r[1]; b=r[2]; a=r[3] !== undefined ? r[3] : 1; r=r[0];
        // No value or null, transparent black.
        } else if (r === undefined || r == null) {
            r=0; g=0; b=0; a=0;
        // One value, grayscale.
        } else if (g === undefined || g == null) {
             a=1; g=r; b=r;
        // Two values, grayscale and alpha.
        } else if (b === undefined || b == null) {
             a=g; g=r; b=r;
        // R, G and B.
        } else if (a === undefined || a == null) {
            a=1;
        }
		// Transform to base 1.
		if (base != 1) {
			r /= base;
			g /= base;
			b /= base;
			a /= base;
		}
		// Transform to base (0.0-1.0).
		if (colorspace != HEX) {
			r = (r < 0)? 0 : (r > 1)? 1 : r;
			g = (g < 0)? 0 : (g > 1)? 1 : g;
			b = (b < 0)? 0 : (b > 1)? 1 : b;
			a = (a < 0)? 0 : (a > 1)? 1 : a;
		}
		// Transform to RGB.
		if (colorspace != RGB) {
			if (colorspace == HEX) {
				var rgb = _hex2rgb(r); r=rgb[0]; g=rgb[1]; b=rgb[2]; a=1;
			}
			if (colorspace == HSB) {
				var rgb = _hsb2rgb(r, g, b); r=rgb[0]; g=rgb[1]; b=rgb[2];
			}
			if (colorspace == HCL) {
				var rgb = _hcl2rgb(r, g, b); r=rgb[0]; g=rgb[1]; b=rgb[2];
			}
		}
        this.r = r;
        this.g = g;
        this.b = b;
        this.a = a;
	},

    rgb: function() {
        return [this.r, this.g, this.b];
    },
    
    rgba: function() {
        return [this.r, this.g, this.b, this.a];
    },
    
    _get: function() {
        var r = Math.round(this.r * 255);
        var g = Math.round(this.g * 255);
        var b = Math.round(this.b * 255);
        return "rgba("+r+", "+g+", "+b+", "+this.a+")";      
    },
    
    copy: function() {
        return new Color(this);
    },
    
    map: function(options) {
        /* Returns array [R,G,B,A] mapped to the given base,
         * e.g. 0-255 instead of 0.0-1.0 which is useful for setting image pixels.
         * Other values than RGBA can be obtained by setting the colorspace (RGB/HSB/HEX).
         */
        var base = options && options.base || 1.0;
        var colorspace = options && options.colorspace || RGB;
        var r = this.r;
        var g = this.g;
        var b = this.b;
        var a = this.a;
        if (colorspace == HEX) {
            return _rgb2hex(r, g, b);
        }
        if (colorspace == HSB) {
            hsb = _rgb2hsb(r, g, b); r=hsb[0]; g=hsb[1]; b=hsb[2];
        }
        if (colorspace == HCL) {
            hcl = _rgb2hcl(r, g, b); r=hcl[0]; g=hcl[1]; b=hcl[2];
        }
		if (colorspace == "premultiplied") {
			rgb = _rgba2rgb(r, g, b, a); r=rgb[0]; g=rgb[1]; b=rgb[2]; a=1;
		}
        if (base != 1) {
            return [r * base, g * base, b * base, a * base];
        }
        return [r, g, b, a];
    },
    
    rotate: function(angle) {
        /* Returns a new color with it's hue rotated on the RYB color wheel.
         */
        var hsb = _rgb2hsb(this.r, this.g, this.b);
        var hsb = _rotateRYB(hsb[0], hsb[1], hsb[2], angle);
        return new Color(hsb[0], hsb[1], hsb[2], this.a, {"colorspace": HSB});
    },
    
    adjust: function(options) {
        /* Returns a new color transformed in HSB colorspace.
         * Hue is added, saturation and brightness are multiplied.
         */
        var hsb = _rgb2hsb(this.r, this.g, this.b);
        hsb[0] += options.hue || 0;
        hsb[1] *= options.saturation || 1;
        hsb[2] *= options.brightness || 1;
        return new Color(Math.mod(hsb[0], 1), hsb[1], hsb[2], this.a, {"colorspace": HSB});
    }
});

function rgb(r, g, b) {
	/* Returns a new Color from R, G, B values (0-255).
	 */ 
    return new Color(r, g, b, 1 * 255, {"base": 255, "colorspace": RGB});
}

function rgba(r, g, b, a) {
	/* Returns a new Color from R, G, B values (0-255) and alpha (0.0-1.0).
	 */ 
    return new Color(r, g, b, a * 255, {"base": 255, "colorspace": RGB});
}

function color(r, g, b, a, options) {
	/* Returns a new Color from R, G, B, A values (0.0-1.0).
	 */ 
    return new Color(r, g, b, a, options);
}

function background(r, g, b, a) {
    /* Sets the current background color.
     */
    if (r !== undefined) {
        var tf = _ctx.currentTransform;
        _ctx.state.background = (r instanceof Color)? new Color(r) : new Color(r, g, b, a);
        _ctx_fill(_ctx.state.background);
        _ctx.setTransform(1, 0, 0, 1, 0, 0); // Identity matrix.
        _ctx.fillRect(0, 0, _ctx._canvas.width, _ctx._canvas.height);
        _ctx.currenTransform = tf;
    }
    return _ctx.state.background;
}

function fill(r, g, b, a) {
    /* Sets the current fill color for drawing primitives and paths.
     */
    if (r !== undefined) {
        _ctx.state.fill = (r instanceof Color || r instanceof Gradient)? r.copy() : new Color(r, g, b, a);
    }
    return _ctx.state.fill;
}
function stroke(r, g, b, a) {
    /* Sets the current stroke color.
     */
    if (r !== undefined) {
        _ctx.state.stroke = (r instanceof Color)? r.copy() : new Color(r, g, b, a);
    }
    return _ctx.state.stroke;
}

function nofill() {
    /* No current fill color.
     */
    _ctx.state.fill = null;
}

function nostroke() {
    /* No current stroke color.
     */
    _ctx.state.stroke = null;
}

function strokewidth(width) {
    /* Sets the outline stroke width.
     */
    if (width !== undefined) {
        _ctx.state.strokewidth = width;
    }
    return _ctx.state.strokewidth;
}

var SOLID  = "solid";
var DOTTED = "dotted";
var DASHED = "dashed";

function strokestyle(style) {
    /* Sets the outline stroke style.
     */
    if (style !== undefined) {
        _ctx.state.strokestyle = style;
    }
    return _ctx.state.strokestyle;
}

var BUTT   = "butt";
var ROUND  = "round";
var SQUARE = "square";

function linecap(cap) {
    /* Sets the outline line caps style.
     */
    if (cap !== undefined) {
        _ctx.state.linecap = cap;
    }
    return _ctx.state.linecap;
}

var noFill = nofill;
var noStroke = nostroke;
var strokeWidth = strokewidth;
var strokeStyle = strokestyle;
var lineCap = linecap;

// fill() and stroke() are heavy operations:
// - they are called often,
// - they copy a Color object,
// - they change the state.
//
// This is the main reason that scripts will run (in overall) 2-8 fps slower than in processing.js.

/*--- COLOR SPACE ----------------------------------------------------------------------------------*/
// Transformations between RGB, HSB, XYZ, LAB, LCH, HEX color spaces.
// Based on: http://www.easyrgb.com/math.php

function _rgb2hex(r, g, b) {
    /* Returns a hexadecimal color string from the given R,G,B values.
     */
    parseHex = function(i) {
        var s = "00";
        s = (i != 0)? i.toString(16).toUpperCase() : s;
        s = (s.length < 2)? "0" + s : s;
        return s;
    }
    return "#"
        + parseHex(Math.round(r * 255)) 
        + parseHex(Math.round(g * 255)) 
        + parseHex(Math.round(b * 255));
}

function _hex2rgb(hex) {
    /* Returns an array [R,G,B] (0.0-1.0) from the given hexadecimal color string.
     */
    hex = hex.replace(/^#/, "");
    if (hex.length < 6) { // hex += hex[-1] * (6-hex.length);
        hex += (new Array(6-hex.length)).join(hex.substr(hex.length-1));
    }
    var r = parseInt(hex.substr(0, 2), 16) / 255;
    var g = parseInt(hex.substr(2, 2), 16) / 255;
    var b = parseInt(hex.substr(4, 2), 16) / 255;
    return [r, g, b];
}

function _rgb2hsb(r, g, b) {
    /* Returns an array [H,S,B] (0.0-1.0) from the given R,G,B values.
     */
    var h = 0;
    var s = 0;
    var v = Math.max(r, g, b);
    var d = v - Math.min(r, g, b);
    if (v != 0) {
        s = d / v;
    }
    if (s != 0) {
             if (r == v) { h = 0 + (g-b) / d; } 
        else if (g == v) { h = 2 + (b-r) / d; } 
        else             { h = 4 + (r-g) / d; }
    }
    h = Math.mod(h / 6.0, 1);
    return [h, s, v];
}

function _hsb2rgb(h, s, v) {
    /* Returns an array [R,G,B] (0.0-1.0) from the given H,S,B values.
     */
    if (s == 0) {
        return [v, v, v];
    }
    h = Math.mod(h, 1) * 6.0;
    var i = Math.floor(h);
    var f = h - i;
    var x = v * (1-s);
    var y = v * (1-s * f);
    var z = v * (1-s * (1-f));
    if (i > 4) {
        return [v, x, y];
    }
    return [[v,z,x], [y,v,x], [x,v,z], [x,y,v], [z,x,v]][parseInt(i)];
}

function _rgb2xyz(r, g, b) {
    /* Returns an array [X,Y,Z] (0-95.047, 0-100, 0-108.883) from the given R,G,B values.
     */
	r = ((r > 0.04045)? Math.pow((r + 0.055) / 1.055, 2.4) : r / 12.92) * 100;
	g = ((g > 0.04045)? Math.pow((g + 0.055) / 1.055, 2.4) : g / 12.92) * 100;
	b = ((b > 0.04045)? Math.pow((b + 0.055) / 1.055, 2.4) : b / 12.92) * 100;
	// Observer = 2°, Illuminant = D65.
	var x = r * 0.4124 + g * 0.3576 + b * 0.1805;
	var y = r * 0.2126 + g * 0.7152 + b * 0.0722;
	var z = r * 0.0193 + g * 0.1192 + b * 0.9505;
	return [x, y, z];
}

function _xyz2rgb(x, y, z) {
    /* Returns an array [R,G,B] (0.0-1.0) from the given X,Y,Z values.
     */
	x /= 100;
	y /= 100;
	z /= 100;
	var r = x *  3.2406 + y * -1.5372 + z * -0.4986;
	var g = x * -0.9689 + y *  1.8758 + z *  0.0415;
	var b = x *  0.0557 + y * -0.2040 + z *  1.0570;
	r = (r > 0.0031308)? 1.055 * Math.pow(r, 1 / 2.4) - 0.055 : 12.92 * r;
	g = (g > 0.0031308)? 1.055 * Math.pow(g, 1 / 2.4) - 0.055 : 12.92 * g;
	b = (b > 0.0031308)? 1.055 * Math.pow(b, 1 / 2.4) - 0.055 : 12.92 * b;
	return [r, g, b];
}

function _xyz2lab(x, y, z) {
    /* Returns an array [L,a,b] (0.0-1.0) from the given X,Y,Z values.
     */
	// Observer = 2°, Illuminant = D65.
	x /=  95.047;
	y /= 100.000;
	z /= 108.883;
	x = (x > 0.008856)? Math.pow(x, 1 / 3) : 7.787 * x + (16 / 116);
	y = (y > 0.008856)? Math.pow(y, 1 / 3) : 7.787 * y + (16 / 116);
	z = (z > 0.008856)? Math.pow(z, 1 / 3) : 7.787 * z + (16 / 116);
	var l = 116 * y - 16;
	var a = 500 * (x - y);
	var b = 200 * (y - z);
	return [l, a, b];
}

function _lab2xyz(l, a, b) {
    /* Returns an array [X,Y,Z] (0-95.047, 0-100, 0-108.883) from the given L,a,b values.
     */
	var y = (l + 16 ) / 116;
	var x = a / 500 + y;
	var z = y - b / 200;
	x = (Math.pow(x, 3) > 0.008856)? Math.pow(x, 3) : (x - 16 / 116) / 7.787;
	y = (Math.pow(y, 3) > 0.008856)? Math.pow(y, 3) : (y - 16 / 116) / 7.787;
	z = (Math.pow(z, 3) > 0.008856)? Math.pow(z, 3) : (z - 16 / 116) / 7.787;
	// Observer = 2°, Illuminant = D65.
	x *=  95.047;
	y *= 100.000;
	z *= 108.883;
	return [x, y, z];
}

function _lab2lch(l, a, b) {
    /* Returns an array [L,C,H] (0.0-1.0) from the given L,a,b values.
     */
	var h = Math.atan2(b, a);
	h = (h > 0)? h / Math.PI * 180 : 360 - Math.abs(h) / Math.PI * 180;
	c = Math.sqrt(a * a + b * b);
	return [l, c, h];
}

function _lch2lab(l, c, h) {
    /* Returns an array [L,a,b] (0.0-1.0) from the given L,C,H values.
     */
	h = h / 180 * Math.PI;
	var a = Math.cos(h) * c;
	var b = Math.sin(h) * c;
	return [l, a, b];
}

function _rgb2hcl(r, g, b) {
    /* Returns an array [H,C,L] (0.0-1.0) from the given R,G,B values.
     */
	var xyz = _rgb2xyz(r, g, b);
	var lab = _xyz2lab(xyz[0], xyz[1], xyz[2]);
	var lch = _lab2lch(lab[0], lab[1], lab[2]);
	lch[0] /= 100;
	lch[1] /= 100;
	lch[2] /= 360;
	return [lch[2], lch[1], lch[0]];
}

function _hcl2rgb(h, c, l) {
    /* Returns an array [R,G,B] (0.0-1.0) from the given H,C,L values.
     */
	h *= 360;
	c *= 100;
	l *= 100;
	var lab = _lch2lab(l, c, h);
	var xyz = _lab2xyz(lab[0], lab[1], lab[2]);
	return _xyz2rgb(xyz[0], xyz[1], xyz[2]);
}

function _rgba2rgb(r, g, b, a, blend) {
    /* Returns an array [R,G,B,1] (0.0-1.0) from the given R,G,B,A values.
     */
    blend = blend || [1,1,1];
    r = r * a + (1 - a) * blend[0];
    g = g * a + (1 - a) * blend[1];
    b = b * a + (1 - a) * blend[2];
    a = 1;
    return [r, g, b, a];
}

function darker(clr, step) {
    /* Returns a copy of the color with a darker brightness.
     */
    if (step === undefined) step = 0.2;
    var hsb = _rgb2hsb(clr.r, clr.g, clr.b);
    var rgb = _hsb2rgb(hsb[0], hsb[1], Math.max(0, hsb[2] - step));
    return new Color(rgb[0], rgb[1], rgb[2], clr.a);
}

function lighter(clr, step) {
    /* Returns a copy of the color with a lighter brightness.
     */
    if (step === undefined) step = 0.2;
    var hsb = _rgb2hsb(clr.r, clr.g, clr.b);
    var rgb = _hsb2rgb(hsb[0], hsb[1], Math.min(1, hsb[2] + step));
    return new Color(rgb[0], rgb[1], rgb[2], clr.a);
}
    
var darken  = darker;
var lighten = lighter;

/*--- COLOR INTERPOLATION --------------------------------------------------------------------------*/

function colors(colors, k, colorspace) {
	/* Returns a new array with k colors,
	   by calculating intermediary colors in the given colorspace (by default, HCL).
	 */
	if (k === undefined) k = 100;
	if (colorspace === undefined) colorspace = HCL;
	var a = Array.map(colors, function(clr) { return clr.map({colorspace: colorspace}); });
	var b = [];
	var x, y, t, n = a.length - 1;
	for (var i=0; i < k-1; i++) {
		x = Math.min(Math.floor(i / k * n), n);
		y = Math.min(x + 1, n);
		t = (i - x * k / n) / (k / n);
		b.push(new Color(
			Math.lerp(a[x][0], a[y][0], t),
			Math.lerp(a[x][1], a[y][1], t),
			Math.lerp(a[x][2], a[y][2], t),
			Math.lerp(a[x][3], a[y][3], t), {colorspace: colorspace}
		));
	}
	if (k > 0) {
		b.push(new Color(a[n][0], a[n][1], a[n][2], a[n][3], {colorspace: colorspace}));
	}
	return b;
}

/*--- COLOR ROTATION -------------------------------------------------------------------------------*/

// Approximation of the RYB color wheel.
// In HSB, colors hues range from 0 to 360, 
// but on the color wheel these values are not evenly distributed. 
// The second tuple value contains the actual value on the wheel (angle).
var _COLORWHEEL = [
    [  0,   0], [ 15,   8], [ 30,  17], [ 45,  26],
    [ 60,  34], [ 75,  41], [ 90,  48], [105,  54],
    [120,  60], [135,  81], [150, 103], [165, 123],
    [180, 138], [195, 155], [210, 171], [225, 187],
    [240, 204], [255, 219], [270, 234], [285, 251],
    [300, 267], [315, 282], [330, 298], [345, 329], [360, 360]
];

function _rotateRYB(h, s, b, angle) {
    /* Rotates the given H,S,B color (0.0-1.0) on the RYB color wheel.
     * The RYB colorwheel is not mathematically precise,
     * but focuses on aesthetically pleasing complementary colors.
     */
    if (angle === undefined) angle = 180;
    h = Math.mod(h * 360, 360);
    // Find the location (angle) of the hue on the RYB color wheel.
    var x0, y0, x1, y1, a;
    var wheel = _COLORWHEEL;
    for (var i=0; i < wheel.length-1; i++) {
        x0 = wheel[i][0]; x1 = wheel[i+1][0];
        y0 = wheel[i][1]; y1 = wheel[i+1][1];
        if (y0 <= h && h <= y1) {
            a = Math.lerp(x0, x1, (h-y0) / (y1-y0));
            break;
        }
    }
    // Rotate the angle and retrieve the hue.
    a = Math.mod(a + angle, 360);
    for (var i=0; i < wheel.length-1; i++) {
        x0 = wheel[i][0]; x1 = wheel[i+1][0];
        y0 = wheel[i][1]; y1 = wheel[i+1][1];
        if (x0 <= a && a <= x1) {
            h = Math.lerp(y0, y1, (a-x0) / (x1-x0));
            break;
        }
    }
    return [h/360.0, s, b];
}

function complement(clr) {
    /* Returns the color opposite on the color wheel.
     * The complementary color contrasts with the given color.
     */
    return clr.rotate(180);
}

function analog(clr, angle, d) {
    /* Returns a random adjacent color on the color wheel.
     * Analogous color schemes can often be found in nature.
     */
    if (angle === undefined) angle = 20;
    if (d === undefined) d = 0.1;
    var hsb = _rgb2hsb(clr.r, clr.g, clr.b);
    var hsb = _rotateRYB(hsb[0], hsb[1], hsb[2], Math.random() * 2 * angle - angle);
    hsb[1] *= 1 - Math.random()*2*d-d;
    hsb[2] *= 1 - Math.random()*2*d-d;
    return new Color(hsb[0], hsb[1], hsb[2], clr.a, {"colorspace":HSB});
}

/*--- COLOR MIXIN ----------------------------------------------------------------------------------*/
// Drawing commands like rect() have optional parameters fill and stroke to set the color directly.

// function _colorMixin({fill: Color(), stroke: Color(), strokewidth: 1.0, strokestyle: SOLID}) 
function _colorMixin(options) {
    var s = _ctx.state;
    var o = options;
    if (o === undefined) {
        return [s.fill, s.stroke, s.strokewidth, s.strokestyle, s.linecap];
    } else {
        return [
            (o.fill !== undefined)? 
                (o.fill instanceof Color || o.fill instanceof Gradient)? 
                    o.fill : new Color(o.fill) : s.fill,
            (o.stroke !== undefined)? 
                (o.stroke instanceof Color)? 
                    o.stroke : new Color(o.stroke) : s.stroke,
            (o.strokewidth !== undefined)? o.strokewidth : 
                (o.strokeWidth !== undefined)? o.strokeWidth : s.strokewidth,
            (o.strokestyle !== undefined)? o.strokestyle : 
                (o.strokeStyle !== undefined)? o.strokeStyle : s.strokestyle,
            (o.linecap !== undefined)? o.linecap : 
                (o.lineCap !== undefined)? o.lineCap : s.linecap
        ];
    }
}

/*--------------------------------------------------------------------------------------------------*/
// Wrappers for _ctx.fill() and _ctx.stroke(), only calling them when necessary.

function _ctx_fill(fill) {
    if (fill && (fill.a > 0 || fill.clr1)) {
        // Ignore transparent colors.
        // Avoid switching _ctx.fillStyle() - we can gain up to 5fps:
        var f = fill._get();
        if (_ctx.state._fill != f) {
            _ctx.fillStyle = _ctx.state._fill = f;
        }
        _ctx.fill();
    }
}

function _ctx_stroke(stroke, strokewidth, strokestyle, linecap) {
    if (stroke && stroke.a > 0 && strokewidth > 0) {
        var s = stroke._get();
        if (_ctx.state._stroke != s) {
            _ctx.strokeStyle = _ctx.state._stroke = s;
        }
        if (_ctx.state._strokestyle != strokestyle && _ctx.setLineDash) {
            _ctx.state._strokestyle = strokestyle;
            switch(strokestyle) {
                case DOTTED: _ctx.setLineDash([1,3]); break;
                case DASHED: _ctx.setLineDash([3,3]); break;
                    default: _ctx.setLineDash([]);
            }
        }
        _ctx.lineWidth = strokewidth;
        _ctx.lineCap = linecap;
        _ctx.stroke();
    }
}

/*##################################################################################################*/

/*--- GRADIENT -------------------------------------------------------------------------------------*/

var LINEAR = "linear";
var RADIAL = "radial";

var Gradient = Class.extend({
//  init: function(clr1, clr2, {type: LINEAR, x: 0, y: 0, spread: 100, angle: 0})
    init: function(clr1, clr2, options) {
        /* A gradient with two colors.
         */
        var o = options || {};
        if (clr1 instanceof Gradient) {
            // One parameter, another gradient object.
            var g = clr1; 
            clr1 = g.clr1.copy(); 
            clr2 = g.clr2.copy(); 
            o = {type: g.type, x: g.x, y: g.y, spread: g.spread, angle: g.angle};
        }
        this.clr1 = (clr1 instanceof Color)? clr1 : new Color(clr1);
        this.clr2 = (clr2 instanceof Color)? clr2 : new Color(clr2);
        this.type = o.type || LINEAR;
        this.x = o.x || 0;
        this.y = o.y || 0;
        this.a = 1.0; // Shapes will only be drawn if color or gradient has alpha > 1.0.
        this.spread = Math.max((o.spread !== undefined)? o.spread : 100, 0);
        this.angle = o.angle || 0;
    },
    
    _get: function(dx, dy) {
        // See also Path.draw() for dx and dy:
        // we use the first MOVETO of the path to make the gradient location relative.
        var x = this.x + (dx || 0);
        var y = this.y + (dy || 0);
        if (this.type == LINEAR) {
            var p = geometry.coordinates(x, y, this.spread, this.angle);
            var g = _ctx.createLinearGradient(x, y, p.x, p.y);
        }
        if (this.type == RADIAL) {
            var g = _ctx.createRadialGradient(x, y, 0, x, y, this.spread);
        }
        g.addColorStop(0.0, this.clr1._get());
        g.addColorStop(1.0, this.clr2._get());
        return g;
    },

    copy: function() {
        return new Gradient(this);
    }
});

function gradient(clr1, clr2, options) {
    return new Gradient(clr1, clr2, options);
}

/*--- SHADOW ---------------------------------------------------------------------------------------*/

function shadow(dx, dy, blur, alpha) {
    /* Sets the current dropshadow, used with all subsequent shapes.
     */
    var s = _ctx.state;
    s.shadow = {
         "dx": (dx !== undefined)? dx : 5,
         "dy": (dy !== undefined)? dy : 5,
       "blur": (blur !== undefined)? blur : 5,
      "alpha": (alpha !== undefined)? alpha : 0.5
    }
    _ctx.shadowOffsetX = s.shadow.dx;
    _ctx.shadowOffsetY = s.shadow.dy;
    _ctx.shadowBlur = s.shadow.blur;  
    _ctx.shadowColor = "rgba(0,0,0," + s.shadow.alpha + ")";
    return s.shadow;
}

function noshadow() {
    _ctx.state.shadow = null;
    _ctx.shadowColor = "transparent";
}

var noShadow = noshadow;

/*##################################################################################################*/

/*--- AFFINE TRANSFORM -----------------------------------------------------------------------------*/
// Based on: T. McCauley, 2009, http://www.senocular.com/flash/tutorials/transformmatrix/

var AffineTransform = Transform = Class.extend({
    
    init: function(transform) {
        /* A geometric transformation in Euclidean space (i.e. 2D)
         * that preserves collinearity and ratio of distance between points.
         * Linear transformations include rotation, translation, scaling, shear.
         */
        if (transform instanceof AffineTransform) {
            this.matrix = transform.matrix.copy();
        } else {
            this.matrix = [1, 0, 0, 0, 1, 0, 0, 0, 1]; // Identity matrix.
        }
    },
    
    copy: function() {
        return new AffineTransform(this);
    },
    
    prepend: function(transform) {
        this.matrix = this._mmult(this.matrix, transform.matrix);
    },
    
    append: function(transform) {
        this.matrix = this._mmult(transform.matrix, this.matrix);
    },
    
    _mmult: function(a, b) {
        /* Returns the 3x3 matrix multiplication of A and B.
         * Note that scale(), translate(), rotate() work with premultiplication,
         * e.g. the matrix A followed by B = BA and not AB.
         */
        return [
            a[0] * b[0] + a[1] * b[3], 
            a[0] * b[1] + a[1] * b[4], 0,
            a[3] * b[0] + a[4] * b[3], 
            a[3] * b[1] + a[4] * b[4], 0,
            a[6] * b[0] + a[7] * b[3] + b[6], 
            a[6] * b[1] + a[7] * b[4] + b[7], 1
        ];
    },
    
    invert: function() {
        /* Multiplying a matrix by its inverse produces the identity matrix.
         */
        var m = this.matrix;
        var d = m[0] * m[4] - m[1] * m[3];
        this.matrix = [
               m[4] / d, 
              -m[1] / d, 0, 
              -m[3] / d, 
               m[0] / d, 0,
              (m[3] * m[7] - m[4] * m[6]) / d, 
             -(m[0] * m[7] - m[1] * m[6]) / d, 1
        ];
    },
    
    inverse: function() {
        var m = this.copy(); m.invert(); return m;
    },
    
    scale: function(x, y) {
        if (y === undefined) y = x;
        this.matrix = this._mmult([x, 0, 0, 0, y, 0, 0, 0, 1], this.matrix);
    },
    
    translate: function(x, y) {
        this.matrix = this._mmult([1, 0, 0, 0, 1, 0, x, y, 1], this.matrix);
    },
    
    rotate: function(angle) {
        var c = Math.cos(Math.radians(angle));
        var s = Math.sin(Math.radians(angle));
        this.matrix = this._mmult([c, s, 0, -s, c, 0, 0, 0, 1], this.matrix);
    },
    
    rotation: function() {
        return Math.mod(Math.degrees(Math.atan2(this.matrix[1], this.matrix[0])) + 360, 360);
    },

    
    apply: function(x, y) {
        return this.transform_point(x, y);
    },

    transform_point: function(x, y) {
        /* Returns the new coordinates of the given point (x,y) after transformation.
         */
        if (y === undefined) { y=x.y; x=x.x; } // One parameter, Point object.
        var m = this.matrix;
        return new Point(
            x * m[0] + y * m[3] + m[6], 
            x * m[1] + y * m[4] + m[7]
        );
    },
    
    transform_path: function(path) {
        /* Returns a Path object with the transformation applied.
         */
        var p = new Path();
        for (var i=0; i < path.array.length; i++) {
            var pt = path.array[i];
            if (pt.cmd == CLOSE) {
                p.closepath();
            } else if (pt.cmd == MOVETO) {
                pt = this.apply(pt);
                p.moveto(pt.x, pt.y);
            } else if (pt.cmd == LINETO) {
                pt = this.apply(pt);
                p.lineto(pt.x, pt.y);
            } else if (pt.cmd == CURVETO) {
                var ctrl1 = this.apply(pt.ctrl1);
                var ctrl2 = this.apply(pt.ctrl2);
                pt = this.apply(pt);
                p.curveto(ctrl1.x, ctrl1.y, ctrl2.x, ctrl2.y, pt.x, pt.y);
            }
        }
        return p;
    },

    transformPoint: function(x, y) {
        return this.transform_point(x, y);
    },
    transformPath: function(path) {
        return this.transform_path(path);
    },
	
	transform: function(path_x, y) {
		return (path_x instanceof Path)?
			this.transform_path(path_x) :
			this.transform_point(path_x, y);
	},
    
    map: function(points) {
        return Array.map(points, function(pt) {
            if (pt instanceof Array) {
                return this.apply(pt[0], pt[1]);
            } else {
                return this.apply(pt.x, pt.y);
            }            
        });
    }
});

/*--- TRANSFORMATIONS ------------------------------------------------------------------------------*/

function push() {
    /* Pushes the transformation state.
     * Subsequent transformations (translate, rotate, scale) remain in effect until pop() is called.
     */
    _ctx.save();
}

function pop() {
    /* Pops the transformation state.
     * This reverts the transformation to before the last push().
     */
    _ctx.restore();
    // Do not reset the color state:
    if (_ctx.state._fill) {
        _ctx.fillStyle = _ctx.state._fill;
    }
    if (_ctx.state._stroke) {
        _ctx.strokeStyle = _ctx.state._stroke;
    }
}

function translate(x, y) {
    /* By default, the origin of the layer or canvas is at the bottom left.
     * This origin point will be moved by (x,y) pixels.
     */
    _ctx.translate(x, y);
}

function rotate(degrees) {
    /* Rotates the transformation state, i.e. all subsequent drawing primitives are rotated.
     * Rotations work incrementally:
     * calling rotate(60) and rotate(30) sets the current rotation to 90.
     */
    _ctx.rotate(degrees / 180 * Math.PI);
}

function scale(x, y) {
    /* Scales the transformation state.
     */
    if (y === undefined) y = x;
    _ctx.scale(x, y);
}

function reset() {
    /* Resets the transform state of the canvas.
     */
    _ctx.restore();
    _ctx.save();
}

/*##################################################################################################*/

/*--- BEZIER MATH ----------------------------------------------------------------------------------*/
// Thanks to Prof. F. De Smedt at the Vrije Universiteit Brussel, 2006.

var Bezier = Class.extend({
    
    // BEZIER MATH:
    
    linePoint: function(t, x0, y0, x1, y1) {
        /* Returns coordinates for the point at t (0.0-1.0) on the line.
         */
        return [
            x0 + t * (x1-x0), 
            y0 + t * (y1-y0)
        ];
    },

    lineLength: function(x0, y0, x1, y1) {
        /* Returns the length of the line.
         */
        var a = Math.pow(Math.abs(x0-x1), 2);
        var b = Math.pow(Math.abs(y0-y1), 2);
        return Math.sqrt(a + b);
    },

    curvePoint: function(t, x0, y0, x1, y1, x2, y2, x3, y3, handles) {
        /* Returns coordinates for the point at t (0.0-1.0) on the curve
         * (de Casteljau interpolation algorithm).
         */
        var dt = 1 - t;
        var x01 = x0*dt + x1*t;
        var y01 = y0*dt + y1*t;
        var x12 = x1*dt + x2*t;
        var y12 = y1*dt + y2*t;
        var x23 = x2*dt + x3*t;
        var y23 = y2*dt + y3*t;
        var h1x = x01*dt + x12*t;
        var h1y = y01*dt + y12*t;
        var h2x = x12*dt + x23*t;
        var h2y = y12*dt + y23*t;
        var x = h1x*dt + h2x*t;
        var y = h1y*dt + h2y*t;
        if (!handles) {
            return [x, y, h1x, h1y, h2x, h2y];
        } else {
            // Include the new handles of pt0 and pt3 (see Bezier.insert_point()).
            return [x, y, h1x, h1y, h2x, h2y, x01, y01, x23, y23];
        }
    },

    curvelength: function(x0, y0, x1, y1, x2, y2, x3, y3, n) {
        /* Returns the length of the curve.
         * Integrates the estimated length of the cubic bezier spline defined by x0, y0, ... x3, y3, 
         * by adding up the length of n linear lines along the curve.
         */
        if (n === undefined) n = 20;
        var length = 0;
        var xi = x0;
        var yi = y0;
        for (var i=0; i < n; i++) {
            var t = (i+1) / n;
            var pt = this.curvePoint(t, x0, y0, x1, y1, x2, y2, x3, y3);
            length += Math.sqrt(
                Math.pow(Math.abs(xi-pt[0]), 2) + 
                Math.pow(Math.abs(yi-pt[1]), 2)
            );
            xi = pt[0];
            yi = pt[1];
        }
        return length;
    },
    
    // BEZIER PATH LENGTH:
    
    segmentLengths: function(path, relative, n) {
        /* Returns an array with the length of each segment in the path.
         * With relative=true, the total length of all segments is 1.0.
         */
        if (n === undefined) n = 20;
        var lengths = [];
        for (var i=0; i < path.array.length; i++) {
            var pt = path.array[i];
            if (i == 0) {
                var close_x = pt.x;
                var close_y = pt.y;
            } else if (pt.cmd == MOVETO) {
                var close_x = pt.x;
                var close_y = pt.y;
                lengths.push(0.0);
            } else if (pt.cmd == CLOSE) {
                lengths.push(this.lineLength(x0, y0, close_x, close_y));
            } else if (pt.cmd == LINETO) {
                lengths.push(this.lineLength(x0, y0, pt.x, pt.y));
            } else if (pt.cmd == CURVETO) {
                lengths.push(this.curvelength(x0, y0, pt.ctrl1.x, pt.ctrl1.y, pt.ctrl2.x, pt.ctrl2.y, pt.x, pt.y, n));
            }
            if (pt.cmd != CLOSE) {
                var x0 = pt.x;
                var y0 = pt.y;
            }
        }
        if (relative == true) {
            var s = Array.sum(lengths);
            if (s > 0) {
                return Array.map(lengths, function(v) { return v/s; });             
            } else {
                return Array.map(lengths, function(v) { return 0.0; });
            }
        }
        return lengths;
    },
    
    length: function(path, segmented, n) {
        /* Returns the approximate length of the path.
         * Calculates the length of each curve in the path using n linear samples.
         * With segmented=true, returns an array with the relative length of each segment (sum=1.0).
         */
        if (n === undefined) n = 20;
        if (!segmented) {
            return sum(this.segmentLengths(path, false, n));
        } else {
            return this.segmentLengths(path, true, n);
        }
    },
    
    // BEZIER PATH POINT:
    
    _locate : function(path, t, segments) {
        /* For a given relative t on the path (0.0-1.0), returns an array [index, t, PathElement],
         * with the index of the PathElement before t, 
         * the absolute time on this segment,
         * the last MOVETO or any subsequent CLOSETO after i.
         */ 
        // Note: during iteration, supplying segmentLengths() yourself is 30x faster.
        if (segments === undefined) segments = this.segmentLengths(path, true);
        for (var i=0; i < path.array.length; i++) {
            var pt = path.array[i];
            if (i == 0 || pt.cmd == MOVETO) {
                var closeto = new Point(pt.x, pt.y);
            }
            if (t <= segments[i] || i == segments.length-1) {
                break;
            }
            t -= segments[i];
        }
        if (segments[i] != 0) t /= segments[i];
        if (i == segments.length-1 && segments[i] == 0) i -= 1;
        return [i, t, closeto];
    },
    
    point: function(path, t, segments) {
        /* Returns the DynamicPathElement at time t on the path.
         * Note: in PathElement, ctrl1 is how the curve started, and ctrl2 how it arrives in this point.
         * Here, ctrl1 is how the curve arrives, and ctrl2 how it continues to the next point.
         */
        var _, i, closeto; _=this._locate(path, t, segments); i=_[0]; t=_[1]; closeto=_[2];
        var x0 = path.array[i].x;
        var y0 = path.array[i].y;
        var pt = path.array[i+1];
        if (pt.cmd == LINETO || pt.cmd == CLOSE) {
            var _pt = (pt.cmd == CLOSE)?
                 this.linePoint(t, x0, y0, closeto.x, closeto.y) :
                 this.linePoint(t, x0, y0, pt.x, pt.y);
            pt = new DynamicPathElement(_pt[0], _pt[1], LINETO);
            pt.ctrl1 = new Point(pt.x, pt.y);
            pt.ctrl2 = new Point(pt.x, pt.y);
        } else if (pt.cmd == CURVETO) {
            var _pt = this.curvePoint(t, x0, y0, pt.ctrl1.x, pt.ctrl1.y, pt.ctrl2.x, pt.ctrl2.y, pt.x, pt.y);
            pt = new DynamicPathElement(_pt[0], _pt[1], CURVETO);
            pt.ctrl1 = new Point(_pt[2], _pt[3]);
            pt.ctrl2 = new Point(_pt[4], _pt[5]);
        }
        return pt;
    },
    
    findPath: function(points, curvature) {
        /* Returns a smooth Path from the given list of points.
         */
        if (curvature === undefined) curvature = 1.0;
        // Don't crash on something straightforward such as a list of [x,y]-arrays.
        if (points instanceof Path) {
            points = points.array;
        }
        for (var i=0; i < points.length; i++) {
            if (points[i] instanceof Array) {
                points[i] = new Point(points[i][0], points[i][1]);
            }
        }
        var path = new Path();
        //  No points: return nothing.
        //  One point: return a path with a single MOVETO-point.
        // Two points: return a path with a single straight line.
        if (points.length == 0) {
            return null;
        }
        if (points.length == 1) {
            path.moveto(points[0].x, points[0].y);
            return path;
        }
        if (points.length == 2) {
            path.moveto(points[0].x, points[0].y);
            path.lineto(points[1].x, points[1].y);
            return path;
        }
        // Zero curvature means path with straight lines.
        if (curvature <= 0) {
            path.moveto(points[0].x, points[0].y)
            for (var i=1; i < points.length; i++) {
                path.lineto(points[i].x, points[i].y);
            }
            return path;
        }
        // Construct the path with curves.
        curvature = Math.min(1.0, curvature);
        curvature = 4 + (1.0 - curvature) * 40;
        // The first point's ctrl1 and ctrl2 and last point's ctrl2
        // will be the same as that point's location;
        // we cannot infer how the path curvature started or will continue.
        var dx = {0: 0}; dx[points.length-1] = 0;
        var dy = {0: 0}; dy[points.length-1] = 0;
        var bi = {1: 1 / curvature};
        var ax = {1: (points[2].x - points[0].x - dx[0]) * bi[1]};
        var ay = {1: (points[2].y - points[0].y - dy[0]) * bi[1]};
        for (var i=2; i < points.length-1; i++) {
            bi[i] = -1 / (curvature + bi[i-1]);
            ax[i] = -(points[i+1].x - points[i-1].x - ax[i-1]) * bi[i];
            ay[i] = -(points[i+1].y - points[i-1].y - ay[i-1]) * bi[i];        
        }
        var r = Array.reversed(Array.range(1, points.length-1));
        for (var i=points.length-2; i > 0; i--) {
            dx[i] = ax[i] + dx[i+1] * bi[i];
            dy[i] = ay[i] + dy[i+1] * bi[i];
        }
        path.moveto(points[0].x, points[0].y);
        for (var i=0; i < points.length-1; i++) {
            path.curveto(
                points[i].x + dx[i],
                points[i].y + dy[i],
                points[i+1].x - dx[i+1],
                points[i+1].y - dy[i+1],
                points[i+1].x,
                points[i+1].y
            );
        }
        return path;
    },
    
    arc: function(x1, y1, x2, y2, angle, extent) {
        /* Returns a list of [x1, y1, x2, y2, x3, y3, x4, y4] coordinates,
         * each a curve from (x1, x1) to (x4, y4) with (x2, y2) and (x3, y3)
         * as their respective Bezier control points.
         */
        angle = -angle; extent = -extent; // clockwise
        var bounds = [x1, y1, x2, y2];
        x1 = Math.min(bounds[0], bounds[2]);
        y1 = Math.min(bounds[1], bounds[3]);
        x2 = Math.max(bounds[0], bounds[2]);
        y2 = Math.max(bounds[1], bounds[3]);
        extent = Math.min(Math.max(extent, -360), +360);
        var n = Math.abs(extent) <= 90 && 1 || Math.ceil(Math.abs(extent) / 90.0);
        var a = extent / n;
        var cx = (x1 + x2) / 2;
        var cy = (y1 + y2) / 2;
        var rx = (x2 - x1) / 2;
        var ry = (y2 - y1) / 2;
        var a2 = Math.radians(a) / 2;
        var kappa = Math.abs(4.0 / 3 * (1 - Math.cos(a2)) / Math.sin(a2));
        var points = [], theta0, theta1, c0, c1, s0, s1, k;
        for (var i=0; i < n; i++) {
            theta0 = Math.radians(angle + (i+0) * a);
            theta1 = Math.radians(angle + (i+1) * a);
            c0 = Math.cos(theta0);
            s0 = Math.sin(theta0);
            c1 = Math.cos(theta1);
            s1 = Math.sin(theta1);
            k = a > 0 && -kappa || kappa;
            points.push([
                cx + rx * c0,
                cy - ry * s0,
                cx + rx * (c0 + k * s0),
                cy - ry * (s0 - k * c0),
                cx + rx * (c1 - k * s1),
                cy - ry * (s1 + k * c1),
                cx + rx * c1,
                cy - ry * s1
            ]);
        }
        return points	
    }
});

_bezier = new Bezier();

/*--- BEZIER PATH ----------------------------------------------------------------------------------*/
// A Path class with lineto(), curveto() and moveto() methods.

var MOVETO  = "moveto";
var LINETO  = "lineto";
var CURVETO = "curveto";
var CLOSE   = "close";

var PathElement = Class.extend({
    
    init: function(x, y, cmd) {
        /* A point in the path, optionally with control handles.
         */
        this.x = x;
        this.y = y;
        this.ctrl1 = new Point(0, 0);
        this.ctrl2 = new Point(0, 0);
        this.radius = 0;
        this.cmd = cmd;        
    },
    
    copy: function() {
        var pt = new PathElement(this.x, this.y, this.cmd);
        pt.ctrl1 = this.ctrl1.copy();
        pt.ctrl2 = this.ctrl2.copy();
        return pt;
    }
});

var DynamicPathElement = PathElement.extend({
    // Not a "fixed" point in the Path, but calculated with Path.point().
});

var Path = BezierPath = Class.extend({
    
    init: function(path) {
        /* A list of PathElements describing the curves and lines that make up the path.
         */
        if (path === undefined) {
            this.array = []; // We can't subclass Array.
        } else if (path instanceof Path) {
            this.array = Array.map(path.array, function(pt) { return pt.copy(); });
        } else if (path instanceof Array) {
            this.array = Array.map(path, function(pt) { return pt.copy(); });
        }
        this._clip = false;
        this._update();
    },
    
    _update: function() {
        this._segments = null;
        this._polygon = null;
    },
    
    copy: function() {
        return new Path(this);
    },
    
    moveto: function(x, y) {
        /* Adds a new point to the path at x, y.
         */
        var pt = new PathElement(x, y, MOVETO);
        pt.ctrl1 = new Point(x, y);
        pt.ctrl2 = new Point(x, y);
        this.array.push(pt);
        this._update();
    },
    
    lineto: function(x, y) {
        /* Adds a line from the previous point to x, y.
         */
        var pt = new PathElement(x, y, LINETO);
        pt.ctrl1 = new Point(x, y);
        pt.ctrl2 = new Point(x, y);
        this.array.push(pt); 
        this._update(); 
    },
    
    curveto: function(x1, y1, x2, y2, x3, y3) { 
        /* Adds a Bezier-curve from the previous point to x3, y3.
         * The curvature is determined by control handles x1, y1 and x2, y2.
         */
        var pt = new PathElement(x3, y3, CURVETO);
        pt.ctrl1 = new Point(x1, y1);
        pt.ctrl2 = new Point(x2, y2);
        this.array.push(pt);
        this._update();
    },
    
    moveTo: function(x, y) { 
        this.moveto(x, y); 
    },
    lineTo: function(x, y) { 
        this.lineto(x, y);
    },
    curveTo: function(x1, y1, x2, y2, x3, y3) { 
        this.curveto(x1, y1, x2, y2, x3, y3); 
    },
    
    closepath: function() {
        /* Adds a line from the previous point to the last MOVETO.
         */
        this.array.push(new PathElement(0, 0, CLOSE));
        this._update();
    },
    
    closePath: function() {
        this.closepath();
    },
    
    rect: function(x, y, width, height, options) {
        /* Adds a rectangle to the path.
         */
        if (!options || options.roundness === undefined) {
            this.moveto(x, y);
            this.lineto(x+width, y);
            this.lineto(x+width, y+height);
            this.lineto(x, y+height);
            this.lineto(x, y);
        } else {
            var curve = Math.min(width * options.roundness, height * options.roundness);
            this.moveto(x, y+curve);
            this.curveto(x, y, x, y, x+curve, y);
            this.lineto(x+width-curve, y);
            this.curveto(x+width, y, x+width, y, x+width, y+curve);
            this.lineto(x+width, y+height-curve);
            this.curveto(x+width, y+height, x+width, y+height, x+width-curve, y+height);
            this.lineto(x+curve, y+height);
            this.curveto(x, y+height, x, y+height, x, y+height-curve);
            this.closepath();
        }
    },
    
    ellipse: function(x, y, width, height) {
        /* Adds an ellipse to the path.
         */
        x -= 0.5 * width; // Center origin.
        y -= 0.5 * height;
        var k = 0.55; // kappa = (-1 + sqrt(2)) / 3 * 4 
        var dx = k * 0.5 * width;
        var dy = k * 0.5 * height;
        var x0 = x + 0.5 * width;
        var y0 = y + 0.5 * height;
        var x1 = x + width;
        var y1 = y + height;
        this.moveto(x, y0);
        this.curveto(x, y0-dy, x0-dx, y, x0, y);
        this.curveto(x0+dx, y, x1, y0-dy, x1, y0);
        this.curveto(x1, y0+dy, x0+dx, y1, x0, y1);
        this.curveto(x0-dx, y1, x, y0+dy, x, y0);
        this.closepath();
    },
    
    arc: function(x, y, radius, angle1, angle2, options) {
        /* Adds an arc to the path,
         * clockwise from angle1 to angle2 along circle (x, y, radius).
         */
        var a1 = angle1 % 360;
        var a2 = angle2;
        if (a2 < a1) {
            a2 = a2 + 360;
        }
        if (options && options.clockwise === false) {
            a2 = a2 % 360 - 360;
        }
        var points = _bezier.arc(x-radius, y-radius, x+radius, y+radius, a1, a2-a1);
        for (var i=0; i < points.length; i++) {
            var pt = points[i];
            if (i == 0) {
                this.moveto(pt[0], pt[1]);
            }
            this.curveto(pt[2], pt[3], pt[4], pt[5], pt[6], pt[7]);
        }
    },
    
//  draw: function({fill: Color(), stroke: Color(), strokewidth: 1.0, strokestyle: SOLID})
    draw: function(options) {
        /* Draws the path.
         */
        _ctx.beginPath();
        if (this.array.length > 0 && this.array[0].cmd != MOVETO) {
            throw "No current point for path (first point must be MOVETO)."
        }
        for (var i=0; i < this.array.length; i++) {
            var pt = this.array[i];
            switch(pt.cmd) {
                case MOVETO:
                    _ctx.moveTo(pt.x, pt.y);
                    break;
                case LINETO: 
                    _ctx.lineTo(pt.x, pt.y);
                    break;
                case CURVETO:
                    _ctx.bezierCurveTo(pt.ctrl1.x, pt.ctrl1.y, pt.ctrl2.x, pt.ctrl2.y, pt.x, pt.y);
                    break;
                case CLOSE: 
                    _ctx.closePath(); 
                    break;
            }
        }
        if (!this._clip) {
            var a = _colorMixin(options); // [fill, stroke, strokewidth, strokestyle, linecap]
            _ctx_fill(a[0]);
            _ctx_stroke(a[1], a[2], a[3], a[4]);
        } else {
            _ctx.clip();
        }
    },
    
    angle: function(t) {
        /* Returns the directional angle at time t (0.0-1.0) on the path.
         */
        // The derive() enumerator is much faster but less precise.
        if (t == 0) {
            var pt0 = this.point(t);
            var pt1 = this.point(t+0.001);
        } else {
            var pt0 = this.point(t-0.001);
            var pt1 = this.point(t);
        }
        return geometry.angle(pt0.x, pt0.y, pt1.x, pt1.y);
    },
    
    point: function(t) {
        /* Returns the DynamicPathElement at time t (0.0-1.0) on the path.
         */
        if (this._segments == null) {
            // Cache the segment lengths for performace.
            this._segments = _bezier.length(this, true, 10);
        }
        return _bezier.point(this, t, this._segments);
    },
    
    points: function(amount, options) {
        /* Returns an array of DynamicPathElements along the path.
         * To omit the last point on closed paths: {end: 1-1.0/amount}
         */
        var start = (options && options.start !== undefined)? options.start : 0.0;
        var end = (options && options.end !== undefined)? options.end : 1.0;
        if (this.array.length == 0) {
            // Otherwise Bezier.point() will raise an error for empty paths.
            return [];
        }
        amount = Math.round(amount);
        // The delta value is divided by amount-1, because we also want the last point (t=1.0)
        // If we don't use amount-1, we fall one point short of the end.
        // If amount=4, we want the point at t 0.0, 0.33, 0.66 and 1.0.
        // If amount=2, we want the point at t 0.0 and 1.0.
        var d = (amount > 1)? (end-start) / (amount-1) : (end-start);
        var a = [];
        for (var i=0; i < amount; i++) {
            a.push(this.point(start + d*i));
        }
        return a;
    },
    
    length: function(precision) {
        /* Returns an approximation of the total length of the path.
         */
        if (precision === undefined) precision = 10;
        return _bezier.length(this, false, precision);
    },
    
    contains: function(x, y, precision) {
        /* Returns true when point (x,y) falls within the contours of the path.
         */
        if (precision === undefined) precision = 100;
        if (this._polygon == null || 
            this._polygon[1] != precision) {
            this._polygon = [this.points(precision), precision];
        }
        return geometry.pointInPolygon(this._polygon[0], x, y);
    }
});

function drawpath(path, options) {
    /* Draws the given Path (or list of PathElements).
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    if (path instanceof Array) {
        path = new Path(path);
    }
    path.draw(options);
}

function autoclosepath(close) {
    /* Paths constructed with beginpath() and endpath() are automatically closed.
     */
    if (close === undefined) close = true;
    _ctx.state.autoclosepath = close;
}

function beginpath(x, y) { 
    /* Starts a new path at (x,y).
     * Functions moveto(), lineto(), curveto() and closepath() 
     * can then be used between beginpath() and endpath() calls.
     */
    _ctx.state.path = new Path();
    _ctx.state.path.moveto(x, y);
}

function moveto(x, y) { 
    /* Moves the current point in the current path to (x,y).
     */
    _ctx.state.path.moveto(x, y);
}

function lineto(x, y) { 
    /* Draws a line from the current point in the current path to (x,y).
     */
    _ctx.state.path.lineto(x, y);
}

function curveto(x1, y1, x2, y2, x3, y3) { 
    /* Draws a curve from the current point in the current path to (x3,y3).
     * The curvature is determined by control handles x1, y1 and x2, y2.
     */
    _ctx.state.path.curveto(x1, y1, x2, y2, x3, y3);
}

function closepath() { 
    /* Closes the current path with a straight line to the last MOVETO.
     */
    _ctx.state.path.closepath();
}

function endpath(options) {
    /* Draws and returns the current path.
     * With {draw:false}, only returns the path so it can be manipulated and drawn with drawpath().
     */
    var s = _ctx.state;
    if (s.autoclosepath) s.path.closepath();
    if (!options || options.draw) {
        s.path.draw(options);
    }
    var p=s.path; s.path=null;
    return p;
}

function findpath(points, curvature) {
    /* Returns a smooth BezierPath from the given list of points.
     */
    return _bezier.findPath(points, curvature);
}

var drawPath = drawpath;
var autoClosePath = autoclosepath;
var beginPath = beginpath;
var moveTo = moveto;
var lineTo = lineto;
var curveTo = curveto;
var closePath = closepath;
var endPath = endpath;
var findPath = findpath;

/*--- POINT ANGLES ---------------------------------------------------------------------------------*/

function derive(points, callback) {
    /* Calls callback(angle, pt) for each point in the given path.
     * The angle represents the direction of the point on the path.
     * This works with Path, Path.points, [pt1, pt2, pt2, ...]
     * For example:
     * derive(path.points(30), function(angle, pt) {
     *     push();
     *     translate(pt.x, pt.y);
     *     rotate(angle);
     *     arrow(0, 0, 10);
     *     pop();
     * });
     * This is useful if you want to have shapes following a path.
     * To put text on a path, rotate the angle by +-90 to get the normal (i.e. perpendicular).
     */
    var p = (points instanceof Path)? points.array : points;
    var n = p.length;
    for (var i=0; i<n; i++) {
        var pt = p[i];
        if (0 < i && i < n-1 && pt.cmd && pt.cmd == CURVETO) {
            // For a point on a curve, the control handle gives the best direction.
            // For PathElement (fixed point in Path), ctrl2 tells us how the curve arrives.
            // For DynamicPathElement (returnd from Path.point()), ctrl1 tell how the curve arrives.
            var ctrl = (pt instanceof DynamicPathElement)? pt.ctrl1 : pt.ctrl2;
            var angle = geometry.angle(ctrl.x, ctrl.y, pt.x, pt.y);
        } else if (0 < i && i < n-1 && pt.cmd && pt.cmd == LINETO && p[i-1].cmd == CURVETO) {
            // For a point on a line preceded by a curve, look ahead gives better results.
            var angle = geometry.angle(pt.x, pt.y, p[i+1].x, p[i+1].y);
        } else if (i == 0 && points instanceof Path) {
            // For the first point in a Path, we can calculate a next point very close by.
            var pt1 = points.point(0.001);
            var angle = geometry.angle(pt.x, pt.y, pt1.x, pt1.y);
        } else if (i == n-1 && points instanceof Path) {
            // For the last point in a Path, we can calculate a previous point very close by.
            var pt0 = points.point(0.999);
            var angle = geometry.angle(pt0.x, pt0.y, pt.x, pt.y)
        } else if (i == n-1 && pt instanceof DynamicPathElement && pt.ctrl1.x != pt.x || pt.ctrl1.y != pt.y) {
            // For the last point in Path.points(), use incoming handle (ctrl1) for curves.
            var angle = geometry.angle(pt.ctrl1.x, pt.ctrl1.y, pt.x, pt.y);
        } else if (0 < i) {
            // For any point, look back gives a good result, if enough points are given.
            var angle = geometry.angle(p[i-1].x, p[i-1].y, pt.x, pt.y);
        } else if (i < n-1) {
            // For the first point, the best (only) guess is the location of the next point.
            var angle = geometry.angle(pt.x, pt.y, p[i+1].x, p[i+1].y);
        } else {
            var angle = 0;
        }
        callback(angle, pt);
    }
}

// Backwards compatibility.
function directed(points, callback) {
    return derive(points, callback);
}

/*--- CLIPPING PATH --------------------------------------------------------------------------------*/

function beginclip(path) {
    /* Enables the given Path as a clipping mask.
       Drawing commands between beginclip() and endclip() are constrained to the shape of the path.
     */
    push();
    path._clip = true;
    drawpath(path);
    path._clip = false;
}

function endclip() {
    pop();
}

var beginClip = beginclip;
var endClip = endclip;

/*--- SUPERSHAPE -----------------------------------------------------------------------------------*/

function supershape(x, y, width, height, m, n1, n2, n3, options) {
    /* Returns a BezierPath constructed using the superformula (Gielis, 2003),
     * which can be used to describe many complex shapes and curves that are found in nature.
     */
    var o = options || {};
    var pts = (o.points !== undefined)? o.points : 100;
    var pct = (o.percentage !== undefined)? o.percentage : 1.0;
    var rng = (o.range !== undefined)? o.range : 2 * Math.PI;
    var path = new Path();
    for (var i=0; i < pts; i++) {
        if (i <= pts * pct) {
            var d  = geometry.superformula(m, n1, n2, n3, i * rng / pts);
            var dx = d[0] * width / 2 + x;
            var dy = d[1] * height / 2 + y;
            if (path.array.length == 0) {
                path.moveto(dx, dy);
            } else {
                path.lineto(dx, dy);
            }
        }
    }
    path.closepath();
    if (o.draw === undefined || o.draw == true) {
        path.draw(o);
    }
    return path;
}

/*##################################################################################################*/

/*--- DRAWING PRIMITIVES ---------------------------------------------------------------------------*/

function line(x0, y0, x1, y1, options) {
    /* Draws a straight line from x0, y0 to x1, y1. 
     * The current stroke, strokewidth and strokestyle are applied.
     */
    var a = _colorMixin(options);
    if (a[1] && a[1].a > 0) {
        _ctx.beginPath();
        _ctx.moveTo(x0, y0);
        _ctx.lineTo(x1, y1);
        _ctx_stroke(a[1], a[2], a[3], a[4]);
    }
}

function arc(x, y, radius, angle1, angle2, options) {
    /* Draws an arc with the center at x, y, clockwise from angle1 to angle2.
     * The current stroke, strokewidth and strokestyle are applied.
     */
    var a = _colorMixin(options);
    if (a[0] && a[0].a > 0 || a[1] && a[1].a > 0) {
        var a1 = Math.radians(angle1);
        var a2 = Math.radians(angle2);
        _ctx.beginPath();
        _ctx.arc(x, y, radius, a1, a2, (options && options.clockwise === false));
        _ctx_stroke(a[1], a[2], a[3], a[4]);
    }
}

function rect(x, y, width, height, options) {
    /* Draws a rectangle with the top left corner at x, y.
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    var a = _colorMixin(options);
    if (a[0] && a[0].a > 0 || a[1] && a[1].a > 0) {
        if (!options || options.roundness === undefined) {
            _ctx.beginPath();
            _ctx.rect(x, y, width, height);
            _ctx_fill(a[0]);
            _ctx_stroke(a[1], a[2], a[3], a[4]);
        } else {
            var p = new Path();
            p.rect(x, y, width, height, options);
            p.draw(options);
        }
    }
}

function triangle(x1, y1, x2, y2, x3, y3, options) {
    /* Draws the triangle created by connecting the three given points.
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    var a = _colorMixin(options);
    if (a[0] && a[0].a > 0 || a[1] && a[1].a > 0) {
        _ctx.beginPath();
        _ctx.moveTo(x1, y1);
        _ctx.lineTo(x2, y2);
        _ctx.lineTo(x3, y3);
        _ctx.closePath();
        _ctx_fill(a[0]);
        _ctx_stroke(a[1], a[2], a[3], a[4]);
    }
}

function ellipse(x, y, width, height, options) {
    /* Draws an ellipse with the center located at x, y.
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    var p = new Path();
    p.ellipse(x, y, width, height);
    p.draw(options);
}

var oval = ellipse;

function arrow(x, y, width, options) {
    /* Draws an arrow with its tip located at x, y.
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    var head = width * 0.4;
    var tail = width * 0.2;
    var p = new Path();
    p.moveto(x, y);
    p.lineto(x-head, y+head);
    p.lineto(x-head, y+tail);
    p.lineto(x-width, y+tail);
    p.lineto(x-width, y-tail);
    p.lineto(x-head, y-tail);
    p.lineto(x-head, y-head);
    p.closepath();
    p.draw(options);
}

function star(x, y, points, outer, inner, options) {
    /* Draws a star with the given points, outer radius and inner radius.
     * The current stroke, strokewidth, strokestyle and fill color are applied.
     */
    if (points === undefined) points = 20;
    if (outer === undefined) outer = 100;
    if (inner === undefined) inner = 50;
    var p = new Path();
    p.moveto(x, y+outer);
    for (var i=0; i < 2 * points + 1; i++) {
        var r = (i % 2 == 0)? outer : inner;
        var a = Math.PI * i / points;
        p.lineto(
            x + r * Math.sin(a), 
            y + r * Math.cos(a)
        );
    };
    p.closepath();
    p.draw(options);
}

// To draw crisp lines, you can use translate(0, 0.5) + line0().
// We call it "0" because floats are rounded to nearest int.

function line0(x1, y1, x2, y2, options) {
    line(
        Math.round(x1), 
        Math.round(y1), 
        Math.round(x2), 
        Math.round(y2), options
    );
}

function rect0(x, y, width, height, options) {
    rect(
        Math.round(x), 
        Math.round(y), 
        Math.round(width), 
        Math.round(height), options
    );
}

/*##################################################################################################*/

/*--- CACHE ----------------------------------------------------------------------------------------*/
// The global cache is a collection of objects that are preloading asynchronously.

var Cache = Class.extend({
    
    init: function() {
        /* A collection of objects (images, scripts, data) that are preloading asynchronously.
         * The Canvas.draw() method is delayed until all objects in the global cache are ready.
         */ 
        this.objects = {};             // Objects in cache, by id.
        this.busy = 0;                 // Objects still loading.
    },
    
    preload: function(id, object, callback) {
        /* Attaches an onload() event to the object and caches it under id.
         */
        object._preload = [id, _cache, callback];
        object.onreadystatechange = function() { if (this.readyState == "complete") { // IE
            if (this._preload) {
                this._preload[1].busy--;
                this._preload[2](this);
                this._preload = null;
            }
        }};
        object.onload = function() {
            if (this._preload) {
                this._preload[1].busy--;
                this._preload[2](this);
                this._preload = null;
            }
        };
        object.onerror = function() {
            _ctx && _ctx._canvas.onerror("Can't load: " + this._preload[0]);
            if (this._preload) {
                this._preload[1].busy--;
            }
        };
        if (id) {
            this.objects[id] = object;
        }
        this.busy++;
    },
    
    script: function(js) {
        /* Caches the given JavaScript file.
         */
        if (this.objects[js]) {
            return;
        } else if (js && !js.substr) {
            throw "Can't load script: " + js;
        } else if (js === undefined) {
            throw "Can't load script: " + js;
        }
        try {
            var script = document.createElement("script");
            script.async = true;
            script.type = "text/javascript";
            script.src = js;
            this.preload(js, script, function(){});
            document.body.appendChild(script);
        } catch(e) {
            throw "Can't load script: " + js + e;
        }
    },
    
    image: function(img) {
        /* Returns a cached <img> element,
         * for the given URL path, URL data, Image, Pixels, Canvas or Buffer.
         */
        if (img === undefined) {
            throw "Can't load image: " + img;
        // Cached.
        } else if (this.objects[img]) {
            return this.objects[img]; 
        // From URL path ("http://").
        } else if (img && img.substr && img.substr(0,5) == "http:") {
            var url = img;
            var src = img;
        // From URL data ("data:image/png"), e.g., Canvas.save().
        } else if (img && img.substr && img.substr(0,5) == "data:") {
            var url = null
            var src = img;
        // From local path ("/g/image.png").
        } else if (img && img.substr && img.substr(0,5) != "file:") {
            var url = img;
            var src = img; 
        // From <img>.
        } else if (img.src && img.complete) {
            var url = null;
            var src = img.src;
        // From Canvas + Buffer.
        } else if (img instanceof Canvas || img instanceof Buffer) {
            var url = null;
            var src = img.save();
        // From HTML <canvas> element.
        } else if (img .getContext) {
            img.complete = true; 
            return img;
        // From Image.
        } else if (img instanceof Image) {
            return this.image(img._img);
        // From Pixels.
        } else if (img instanceof Pixels) {
            return img._img._img;
        } else {
            throw "Can't load image: " + img;
        }
        // Cache image source.
        // URL paths, URL data, Canvas and Buffer get an onload() event.
        img = document.createElement("img");
        img._owners = [];
        this.preload(url, img, function(img) {
            // Set Image owner size. 
            // There can be multiple owners displaying the same image.
            for (var i=0; i < img._owners.length; i++) {
                var o = img._owners[i];
                if (o && o.width  == null) o.width  = img.width;
                if (o && o.height == null) o.height = img.height;
            }
            img._owners = []; // Remove reference.            
        });
        // A canvas with cross-domain images becomes tainted:
        // https://developer.mozilla.org/en/CORS_Enabled_Image
        // This disables ctx.toDataURL() and ctx.getImageData().
        // This disables Pixels and Buffer.
        //img.crossOrigin = "";
        img.src = src;
        return img;
    }
});

// Global cache:
var _cache = new Cache();

/*--- INCLUDE --------------------------------------------------------------------------------------*/

function include(url) {
    /* Imports the given JavaScript library,
     * from a local path (e.g., "graph.js") or a remote URL (e.g., "http://domain.com/graph.js").
     */
    _cache.script(url);
}

var require = require || include;

/*--- ASYNCHRONOUS REQUEST -------------------------------------------------------------------------*/

var AsynchronousRequest = Class.extend({
    
    init: function(url, data) {
        /* Loads the given URL in the background using XMLHTTPRequest.
         * AsynchronousRequest.done is False as long as it is busy.
         * AsynchronousRequest.value contains the response value once done.
         */
        if (window.XMLHttpRequest) var q = new XMLHttpRequest();
        if (window.ActiveXObject)  var q = new ActiveXObject("Microsoft.XMLHTTP");
        q.onreadystatechange = function() {
            if (q.readyState == 4 && q.status == 200) this._fetch(q);
        }
        if (data) {
            q.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
            q.open("POST", url, true);
            q.send(data);
        } else {
            q.open("GET", url, true);
            q.send();            
        }
        this.value = null;
        this.done = false;
    },
    
    _fetch: function(q) {
        this.value = q.responseText;
        this.done = true;
    }
});

function asynchronous(url, data) {
    return new AsynchronousRequest(url, data);
}

/*##################################################################################################*/

/*--- IMAGE ----------------------------------------------------------------------------------------*/

var Image = Class.extend({

//  init: function(url, {x: 0, y: 0, width: null, height: null, alpha: 1.0})
    init: function(url, options) {
        /* A image that can be drawn at a given position.
         */
        var o = options || {};
        this._url = url;
        this._img = _cache.image(url);
        this.x = o.x || 0;
        this.y = o.y || 0;
        this.width = (o.width !== undefined)? o.width : null;
        this.height = (o.height !== undefined)? o.height : null;
        this.alpha = (o.alpha !== undefined)? o.alpha : 1.0;
        // If no width or height is given (undefined | null),
        // use the dimensions of the source <img>.
        // If the <img> is still loading, this happens with a delay (see Images.load()).
        if (this._img._owners && !this._img.complete) {
            this._img._owners.push(this);
        }
        if (this.width == null && this._img.complete) {
            this.width = this._img.width;
        }
        if (this.height == null && this._img.complete) {
            this.height = this._img.height;
        }
    },
    
    copy: function() {
        return new Image(this._url, {
            x: this.x, y: this.y, width: this.width, height: this.height, alpha: this.alpha
        });
    },

//  draw: function(x, y, {width: null, height: null, alpha: 1.0})
    draw: function(x, y, options) {
        /* Draws the image.
         * The given parameters (if any) override the image's attributes.
         */
        var o = options || {};
        var w = (o.width !== undefined && o.width != null)? o.width : this.width;
        var h = (o.height !== undefined && o.height != null)? o.height : this.height;
        var a = (o.alpha !== undefined)? o.alpha : this.alpha;
        x = (x || x === 0)? x : this.x;
        y = (y || y === 0)? y : this.y;
        if (this._img.complete && w && h && a > 0) {
            if (a >= 1.0) {
                _ctx.drawImage(this._img, x, y, w, h);
            } else {
                _ctx.globalAlpha = a;
                _ctx.drawImage(this._img, x, y, w, h);
                _ctx.globalAlpha = 1.0;
            }
        }
    },
    
    busy: function() {
        return !this._img.complete; // Still loading?
    }
});

function image(img, x, y, options) {
    /* Draws the image at (x,y), scaling it to the given width and height.
     * The image's transparency can be set with alpha (0.0-1.0).
     */
    img = (img instanceof Image)? img : new Image(img);
    if (!options || options.draw != false) {
        img.draw(x, y, options);
    }
    return img;
}

function imagesize(img) {
    /* Returns an array [width, height] with the image dimensions.
     */
    img = (img instanceof Image)? img : new Image(img);
    return [img._img.width, img._img.height];
}

var imageSize = imagesize;

/*##################################################################################################*/

/*--- PIXELS ---------------------------------------------------------------------------------------*/

var Pixels = Class.extend({
    
    init: function(img) {
        /* An array of RGBA color values (0-255) for each pixel in the given image.
         * Pixels.update() must be called to reflect any changes to Pixels.array.
         * The Pixels object can be passed to the image() function.
         * The original image will not be modified.
         * Throws a security error for remote (cross-domain) images.
         */
        img = (img instanceof Image)? img : new Image(img);
        this._img = img;
        this._element = document.createElement("canvas");
        this._element.width = this.width = img._img.width;
        this._element.height = this.height = img._img.height;
        this._ctx = this._element.getContext("2d");
        this._ctx.drawImage(img._img, 0, 0);
        this._data = this._ctx.getImageData(0, 0, this.width, this.height);
        this.array = this._data.data;
    },
    
    copy: function() {
        return new Pixels(this._img);
    },
    
    get: function(i) {
        /* Returns array [R,G,B,A] with channel values between 0-255 from pixel i.
         * var rgba = Pixels.get[i];
         * var clr = new Color(rgba, {base:255});
         */
        i*= 4;
        return [this.array[i+0], this.array[i+1], this.array[i+2], this.array[i+3]]
    },
    
    set: function(i, rgba) {
        /* Sets pixel i to the given array [R,G,B,A] with values 0-255.
         * var clr = new Color(0,0,0,1);
         * Pixels.set(i, clr.map({base:255}));
         */
        i*= 4;
        this.array[i+0] = rgba[0];
        this.array[i+1] = rgba[1];
        this.array[i+2] = rgba[2];
        this.array[i+3] = rgba[3];
    },
    
    map: function(callback) {
        /* Applies a function to each pixel.
         * Function takes a list of R,G,B,A channel values and must return a similar list.
         */
        for (var i=0; i < this.width * this.height; i++) {
            this.set(i, callback(this.get(i)));
        }
    },
    
    update: function() {
        /* Pixels.update() must be called to refresh the image.
         */
        this._ctx.putImageData(this._data, 0, 0);
        this._img = new Image(this._element);
    },
    
    image: function() {
        return this._img;
    }
});

function pixels(img) {
    return new Pixels(img);
}

/*##################################################################################################*/

/*--- FONT -----------------------------------------------------------------------------------------*/

var NORMAL = "normal";
var BOLD   = "bold";
var ITALIC = "italic"

function font(fontname, fontsize, fontweight) {
    /* Sets the current font and/or fontsize.
     */
    if (fontname !== undefined) _ctx.state.fontname = fontname;
    if (fontsize !== undefined) _ctx.state.fontsize = fontsize;
    if (fontweight !== undefined) _ctx.state.fontweight = fontweight;
    return _ctx.state.fontname;
}

function fontsize(fontsize) {
    /* Sets the current fontsize in points.
     */
    if (fontsize !== undefined) _ctx.state.fontsize = fontsize;
    return _ctx.state.fontsize;
}

function fontweight(fontweight) {
    /* Sets the current font weight (BOLD, ITALIC, BOLD+ITALIC).
     */
    if (fontweight !== undefined) _ctx.state.fontweight = fontweight;
    return _ctx.state.fontweight;
}

function lineheight(lineheight) {
    /* Sets the vertical spacing between lines of text.
     * The given size is a relative value: lineheight 1.2 for fontsize 10 means 12.
     */
    if (lineheight !== undefined) _ctx.state.lineheight = lineheight;
    return _ctx.state.lineheight;
}

var fontSize = fontsize;
var fontWeight = fontweight;
var lineHeight = lineheight;

/*--- FONT MIXIN -----------------------------------------------------------------------------------*/
// The text() function has optional parameters font, fontsize, fontweight, bold, italic, lineheight and align.

function _fontMixin(options) {
    var s = _ctx.state;
    var o = options;
    if (options === undefined) {
        return [s.fontname, s.fontsize, s.fontweight, s.lineheight];
    } else {
        return [
            (o.font)? o.font : s.fontname,
            (o.fontsize !== undefined)? o.fontsize : 
                (o.fontSize !== undefined)? o.fontSize : s.fontsize,
            (o.fontweight !== undefined)? o.fontweight : 
                (o.fontWeight !== undefined)? o.fontWeight : s.fontweight,
            (o.lineheight !== undefined)? o.lineheight : 
                (o.lineHeight !== undefined)? o.lineHeight : s.lineheight
        ];
    }
}

/*--- TEXT -----------------------------------------------------------------------------------------*/

function _ctx_font(fontname, fontsize, fontweight) {
    // Wrappers for _ctx.font, only calling it when necessary.
    if (fontweight.length > ITALIC.length && fontweight == BOLD+ITALIC || fontweight == ITALIC+BOLD) {
        fontweight = ITALIC + " " + BOLD;
    }
    _ctx.font = fontweight + " " + fontsize + "pt " + fontname;
}

function str(v) {
    return v.toString();
}

function text(str, x, y, options) {
    /* Draws the string at the given position.
     * Lines of text will be split at \n.
     * The text will be displayed with the current state font(), fontsize(), fontweight().
     */
    var a1 = _colorMixin(options);
    var a2 = _fontMixin(options);
    if (a1[0] && a1[0].a > 0) {
        var f = a1[0]._get();
        if (_ctx.state._fill != f) {
            _ctx.fillStyle = _ctx.state._fill = f;
        }
        _ctx_font(a2[0], a2[1], a2[2]);
        var lines = str.toString().split("\n");
        for (var i=0; i<lines.length; i++) {
            _ctx.fillText(lines[i], x, y + i*a2[1]*a2[3]);
        }
    }
}

function textmetrics(str, options) {
    /* Returns array [width, height] for the given text.
     */
    var a = _fontMixin(options);
    var w = 0;
    _ctx_font(a[0], a[1], a[2]);
    var lines = str.toString().split("\n");
    for (var i=0; i<lines.length; i++) {
        w = Math.max(w, _ctx.measureText(lines[i]).width);
    }
    return [w, a[1] + a[1]*a[3]*(lines.length-1)];
}

function textwidth(str, options) {
    /* Returns the width of the given text.
     */
    return textmetrics(str, options)[0];
}

function textheight(str, options) {
    /* Returns the height of the given text.
     */
    return textmetrics(str, options)[1];
}

var textMetrics = textmetrics;
var textWidth = textwidth;
var textHeight = textheight;

/*##################################################################################################*/

/*--- UTILITY FUNCTIONS ----------------------------------------------------------------------------*/

var _RANDOM_MAP = [90.0, 9.00, 4.00, 2.33, 1.50, 1.00, 0.66, 0.43, 0.25, 0.11, 0.01];

function _rndExp(bias) { 
    if (bias === undefined) bias = 0.5;
    bias = Math.max(0, Math.min(bias, 1)) * 10;
    var i = parseInt(Math.floor(bias)); // bias*10 => index in the _map curve.
    var n = _RANDOM_MAP[i];             // If bias is 0.3, rnd()**2.33 will average 0.3.
    if (bias < 10) {
        n += (_RANDOM_MAP[i+1]-n) * (bias-i);
    }
    return n;
}

function random(v1, v2, bias) {
    /* Returns a number between v1 and v2, including v1 but not v2.
     * The bias (0.0-1.0) represents preference towards lower or higher numbers.
     */
    if (v1 === undefined) v1 = 1.0;
    if (v2 === undefined) {
        v2=v1; v1=0;
    }
    if (bias === undefined) {
        var r = Math.random();
    } else {
        var r = Math.pow(Math.random(), _rndExp(bias));
    }
    return r * (v2-v1) + v1;
}

var _NOISE_P = []; // Noise permutation table.
var _NOISE_G = []; // Noise gradient (2D = 8 directions).

function noise(x, y, m) {
    /* Returns a smooth value between -1.0 and 1.0.
     * Since the 2D space is infinite, the actual (x,y) coordinates do not matter.
     * Smaller steps between successive coordinates yield smoother noise (e.g., 0.01-0.1).
     */
    // Based on: http://www.angelcode.com/dev/perlin/perlin.html
    if (m === undefined) m = 1.5;
    if (_NOISE_P.length == 0) {
        _NOISE_P = Array.shuffle(Array.range(256));
        _NOISE_P = _NOISE_P.concat(_NOISE_P);
        _NOISE_G = [[-1, +1], [+0, +1], [+1, +1], [-1, +0], [+1, +0], [-1, -1], [+0, -1], [+1, -1]];
    }
    var X = Math.floor(x) & 255;
    var Y = Math.floor(y) & 255;
    x -= Math.floor(x);
    y -= Math.floor(y);
    var u = x * x * x * (x * (x * 6 - 15) + 10); // fade
    var v = y * y * y * (y * (y * 6 - 15) + 10);
    var n = Math.mix(
        Math.mix(Math.dot(_NOISE_G[_NOISE_P[X   + _NOISE_P[Y  ]] % 8], [x  , y  ]), 
                 Math.dot(_NOISE_G[_NOISE_P[X+1 + _NOISE_P[Y  ]] % 8], [x-1, y  ]), u),
        Math.mix(Math.dot(_NOISE_G[_NOISE_P[X   + _NOISE_P[Y+1]] % 8], [x  , y-1]), 
                 Math.dot(_NOISE_G[_NOISE_P[X+1 + _NOISE_P[Y+1]] % 8], [x-1, y-1]), u), v);
    return (Math.clamp(n * m, -1, +1) + 1) * 0.5; // 0.0-1.0
}

function grid(cols, rows, colWidth, rowHeight, shuffled) {
    /* Returns an array of Points for the given number of rows and columns.
     * The space between each point is determined by colwidth and colheight.
     */
    if (colWidth === undefined) colWidth = 1;
    if (rowHeight === undefined) rowHeight = 1;
    rows = Array.range(parseInt(rows));
    cols = Array.range(parseInt(cols));
    if (shuffled) {
        Array.shuffle(rows);
        Array.shuffle(cols);
    }
    var a = [];
    for (var y=0; y < rows.length; y++) {
        for (var x=0; x < cols.length; x++) {
            a.push(new Point(x*colWidth, y*rowHeight));
        }
    }
    return a;
}

/*##################################################################################################*/

/*--- MOUSE ----------------------------------------------------------------------------------------*/

function absOffset(element) {
    /* Returns the absolute position of the given element in the browser.
     */
    var x = y = 0;
    if (element.offsetParent) {
        do {
            x += element.offsetLeft;
            y += element.offsetTop;
        } while (element = element.offsetParent);
    }
    return [x,y];
}

// Mouse cursors:
var DEFAULT = "default";
var HIDDEN  = "none";
var CROSS   = "crosshair";
var HAND    = "pointer";
var POINTER = "pointer";
var DRAG    = "move";
var TEXT    = "text";
var WAIT    = "wait";

var Mouse = Class.extend({
    
    init: function(element) {
        /* Keeps track of the mouse position on the given element.
         */
        this.parent = element; element._mouse=this;
        this.x = 0;
        this.y = 0;
        this.relative_x = this.relativeX = 0;
        this.relative_y = this.relativeY = 0;
        this.pressed = false;
        this.dragged = false;
        this.drag = {
            "x": 0,
            "y": 0
        };
        this.scroll = 0;
        this._out = function() {
            // Returns true if not inside Mouse.parent.
            return !(0 <= this.x && this.x <= this.parent.offsetWidth && 
                     0 <= this.y && this.y <= this.parent.offsetHeight);
        }
        var eventScroll = function(e) {
            // Create parent onmousewheel event (set Mouse.scroll).
            // Fire Mouse.onscroll().
            var m = this._mouse;
            m.scroll += Math.sign(e.wheelDelta);
            if (m.onscroll && m.onscroll(m) === false) {
                e.preventDefault();
                e.stopPropagation();
            }
        };
        var eventDown = function(e) {
            // Create parent onmousedown event (set Mouse.pressed).
            // Fire Mouse.onpress().
            var m = this._mouse;
            if (e.touches !== undefined) {
                // TouchStart (iPad).
                e.preventDefault();
            }
            m.pressed = true;
            m._x0 = m.x;
            m._y0 = m.y;
            m.onpress(m);
        };
        var eventUp = function(e) {
            // Create parent onmouseup event (reset Mouse state).
            // Fire Mouse.onrelease() if inside parent bounds.
            var m = this._mouse;
            m.pressed = false;
            m.dragged = false;
            m.drag.x = 0;
            m.drag.y = 0;
            m.scroll = 0;
            m.onrelease(m, m._out());
        };
        var eventMove = function(e) {
            // Create parent onmousemove event (set Mouse position & drag).
            // Fire Mouse.onmove() if mouse pressed and inside parent bounds.
            // Fire Mouse.ondrag() if mouse pressed.
            var m = this._mouse;
            var o1 = document.documentElement || document.body;
            var o2 = absOffset(this);
            if (e.touches !== undefined) {
                // TouchEvent (iPad).
                m.x = e.touches[0].pageX;
                m.y = e.touches[0].pageY;
            } else {
                // MouseEvent.
                m.x = (e.pageX || (e.clientX + o1.scrollLeft)) - o2[0];
                m.y = (e.pageY || (e.clientY + o1.scrollTop)) - o2[1];
            }
            if (m.pressed) {
                m.dragged = true;
                m.drag.x = m.x - m._x0;
                m.drag.y = m.y - m._y0;
            }
            m.relative_x = m.relativeX = m.x / m.parent.offsetWidth;
            m.relative_y = m.relativeY = m.y / m.parent.offsetHeight;
            if (m.pressed) {
                m.ondrag(m);
            } else if (!m._out()) {
                m.onmove(m);
            }
        };
        // Bind mouse and multi-touch events:
        attachEvent(element, "mousewheel", eventScroll);
        attachEvent(element, "mousedown" , eventDown);
        attachEvent(element, "touchstart", eventDown);
        attachEvent(window,  "mouseup"   , Function.closure(this.parent, eventUp)); 
        attachEvent(window,  "touchend"  , Function.closure(this.parent, eventUp));
        attachEvent(window,  "mousemove" , Function.closure(this.parent, eventMove));
        attachEvent(window,  "touchmove" , Function.closure(this.parent, eventMove));
    },
    
    // These can be patched with a custom function:
    onscroll:  function(mouse) {},
    onpress:   function(mouse) {},
    onrelease: function(mouse, out) {}, // With out=true if mouse outside canvas.
    onmove:    function(mouse) {},
    ondrag:    function(mouse) {},
    
    cursor: function(mode) {
        /* Sets the mouse cursor (DEFAULT, HIDDEN, CROSS, POINTER, TEXT or WAIT).
         */
        if (mode !== undefined) {
            this.parent.style.cursor = mode;
        }
        return this.parent.style.cursor;
    }
});

/*--- CANVAS ---------------------------------------------------------------------------------------*/

function _uid() {
    // Returns a unique number.
    if (_uid.i === undefined) _uid.i=0;
    return ++_uid.i;
}

function _unselectable(element) {
    // Disables text dragging on the given element.
    element.onselectstart = function() { 
        return false; 
    };
    element.unselectable = "on";
    element.style.MozUserSelect = "none";
    element.style.cursor = "default";
}

window._requestFrame = function(callback, canvas, fps) {
    var f = window.requestAnimationFrame
         || window.webkitRequestAnimationFrame
         || window.mozRequestAnimationFrame
         || window.msRequestAnimationFrame
         || window.oRequestAnimationFrame
         || function(callback, element) { return window.setTimeout(callback, 1000 / (fps || 60)); };
    // When requestFrame() calls Canvas._draw() directly, the "this" keyword will be detached.
    // Make "this" available inside Canvas._draw() by binding it:
    return f(Function.closure(canvas, callback), canvas.element);
};

window._clearFrame = function(id) {
    var f = window.cancelAnimationFrame
         || window.webkitCancelAnimationFrame
         || window.webkitCancelRequestAnimationFrame
         || window.mozCancelAnimationFrame
         || window.mozCancelRequestAnimationFrame
         || window.msCancelAnimationFrame
         || window.msCancelRequestAnimationFrame
         || window.oCancelAnimationFrame
         || window.oCancelRequestAnimationFrame
         || window.clearTimeout;
    return f(id);
};

// Current graphics context.
// It is the Canvas that was last created, OR
// it is the Canvas that is preparing to call Canvas.draw(), OR
// it is the Buffer that has called Buffer.push().
var _ctx = null;

var G_vmlCanvasManager; // Needed with excanvas.js

var Canvas = Class.extend({
    
    init: function(element, width, height, options) {
        /* Interface to the HTML5 <canvas> element.
         * Drawing starts when Canvas.run() is called.
         * The draw() method must be overridden with your own drawing commands, which will be executed each frame.
         */
        if (options === undefined) {
            options = {};
        }
        if (!element) {
            element = document.createElement("canvas");
        }
        if (!element.getContext && typeof(G_vmlCanvasManager) != "undefined") {
            element = G_vmlCanvasManager.initElement(element);
        }
        if (width !== undefined && 
            width !== null) {
            element.width = width;
        }
        if (height !== undefined && 
            height !== null) {
            element.height = height;
        }
        _unselectable(element);
        this.id = "canvas" + _uid();
        this.element = element; 
        this.element.style["-webkit-tap-highlight-color"] = "rgba(0,0,0,0)";
        this.element.canvas = this;
        this._ctx = this.element.getContext("2d");
        this._ctx._canvas = this;
        this.focus();
        this.mouse = (options.mouse != false)? new Mouse(this.element) : null;
        this.width = this.element.width;
        this.height = this.element.height;
        this.frame = 0;
        this.fps = 0;
        this.dt = 0;
        this._time = {start: null, current: null};
        this._step = 0;
        this._active = false;
        this._widgets = [];
        this.variables = [];
        this._resetState();
    },
        
    _resetState: function() {
        // Initialize color state: current background, current fill, ...
        // The state is applied to each shape when drawn - see _ctx_fill(), _ctx_stroke() and _ctx_font().
        // Drawing commands such as rect() have optional parameters 
        // that can override the state - see _colorMixin().
        _ctx.state = {
                 "path": null,
        "autoclosepath": false,
           "background": null,
                 "fill": new Color(0,0,0,1),
               "stroke": null,
          "strokewidth": 1.0,
          "strokestyle": SOLID,
               "shadow": null,
             "fontname": "sans-serif",
             "fontsize": 12,
           "fontweight": NORMAL,
           "lineheight": 1.2
        }
    },
    
    _resetWidgets: function() {
        // Resets canvas widgets, removing the variables and <input> elements.
        for (var i=0; i < this._widgets.length; i++) {
            var w = this._widgets[i];
            var e = w.element.parentNode;
            e.parentNode.removeChild(e);
            delete this[w.name];
        }
        var p = document.getElementById(this.id + "_widgets");
        if (p) p.parentNode.removeChild(p);
        this._widgets = [];
        this.variables = [];
    },
    
    focus: function() {
        _ctx = this._ctx; // Set the current graphics context.
    },
    
    size: function(width, height) {
        this.width = this.element.width = width;
        this.height = this.element.height = height;
    },
    
    setup: function() {
        
    },
    
    draw: function() {
        this.clear();
    },
    
    stop: function() {
        this._stop();
    },
    
    clear: function() {
        /* Clears the previous frame from the canvas.
         */
        this._ctx.clearRect(0, 0, this.width, this.height);
    },
    
    _setup: function() {
        this._resetState();
        this.focus();
        push();
        try {
            this.setup(this);
        } catch(e) {
            this.onerror(e); throw e;
        }
        pop();
    },
    
    _draw: function() {
        if (this._active == false && !(this._step > this.frame)) {
            // Drawing halts after stop(), pause() or step().
            // If step() is called, we first need to draw one more frame.
            return;
        }
        var t = new Date;
        this.fps = this.frame * 1000 / (t - this._time.start) || 1;
        this.fps = Math.round(this.fps * 100) / 100;
        this.dt = (t - this._time.current) / 1000;
        this._time.current = t;
        this._step = 0;
        this.frame++;
        this.focus()
        push();
        this._resetState();
        try {
            this.draw(this);
        } catch(e) {
            this.onerror(e); throw e;
        }
        pop();
        this._scheduled = window._requestFrame(this._draw, this);
    },

    _stop: function() {
        /* Stops the animation.
           When run() is called subsequently, the animation will restart from the first frame.
         */
        if (this._scheduled !== undefined) {
            window._clearFrame(this._scheduled);
        }
        this._active = false;
        this._resetWidgets();
        this.frame = 0;
    },

    run: function() {
        /* Starts drawing the canvas.
         * Canvas.setup() will be called once during initialization.
         * Canvas.draw() will be called each frame. 
         * Canvas.clear() needs to be called explicitly to clear the previous frame drawing.
         * Canvas.stop() stops the animation, but doesn't clear the canvas.
         */
        this._active = true;
        this._time.start = new Date();
        this._time.current = this._time.start;
        if (this.frame == 0) {
            this._setup();
        }
        // Delay Canvas.draw() until the cached images are done loading
        // (for example, Image objects created during Canvas.setup()).
        var _preload = function() {
            if (_cache.busy > 0) { setTimeout(Function.closure(this, _preload), 10); return; }
            this._draw(); 
        }
        _preload.apply(this);
    },
    
    pause: function() {
        /* Pauses the animation at the current frame.
         */
        if (this._scheduled !== undefined) {
            window._clearFrame(this._scheduled);
        }
        this._active = false;
    },

    step: function() {
        /* Draws one frame and pauses.
         */
        this._step = this.frame+1;
        this.run();
        this.pause();
    },
    
    active: function() {
        /* Returns true if the animation is running.
         */
        return this._active;
    },

    image: function() {
        /* Returns a new Image with the contents of the canvas.
         * Throws a security error if the canvas contains remote (cross-domain) images.
         */
        return new Image(this.element, {width: this.width, height: this.height});
    },
    
    save: function() {
        /* Returns a data:image/png base64-encoded string.
         * Throws a security error if the canvas contains remote (cross-domain) images.
         */
        //var w = window.open();
        //w.document.body.innerHTML = "<img src=\"" + Canvas.save() + "\" />";
        return this.element.toDataURL("image/png");
    },
    
    widget: function(variable, type, options) {
        widget(this, variable, type, options);
    },
    
    onerror: function(error) {
        // Called when an error occurs in Canvas.draw() or Canvas.setup().
    },
    
    onprint: function(string) {
        // Called when the print() function is called.
    }
});

function size(width, height) {
    /* Sets the width and the height of the canvas.
     */
    _ctx._canvas.size(width, height);
}

function print() {
    /* Calls Canvas.onprint() with the given arguments joined as a string.
     */
    if (_ctx) _ctx._canvas.onprint(Array.prototype.slice.call(arguments).join(" "));
}

/*##################################################################################################*/

/*--- OFFSCREEN BUFFER -----------------------------------------------------------------------------*/

var OffscreenBuffer = Buffer = Canvas.extend({
    
    init: function(width, height) {
        /* A hidden canvas, useful for preparing procedural images.
         */
        this._ctx_stack = [_ctx];
        this._super(document.createElement("canvas"), width, height, {mouse:false});
        // Do not set the Buffer as current graphics context 
        // (call Buffer.push() explicitly to do this):
        _ctx = this._ctx_stack[0];
    },
    
    _setup: function() {
        this.push();
        this._super();
        this.pop();
    },
    _draw: function() {
        this.push();
        this._super();
        this.pop();
    },
        
    push: function() { 
        /* Between push() and pop(), all drawing is done offscreen in OffscreenBuffer.image().
         * The offscreen buffer has its own transformation state,
         * so any translate(), rotate() etc. does not affect the onscreen canvas.
         */
        this._ctx_stack.push(_ctx); _ctx=this._ctx;
    },
    
    pop: function() {
        /* Reverts to the onscreen canvas. 
         * The contents of the offscreen buffer can be retrieved with OffscreenBuffer.image().
         */
        _ctx = this._ctx_stack.pop();
    },
    
    render: function() {
        /* Executes the drawing commands in OffscreenBuffer.draw() offscreen and returns image.
         */
        this.run();
        this._stop();
        return this.image();
    },
    
    reset: function(width, height) {
        if (width !== undefined && height !== undefined) {
            this.clear();
            this.size(width, height);
        }
    }
});

function render(callback, width, height) {
    /* Returns an Image object from a function containing drawing commands (i.e. a procedural image).
     * This is useful when, for example, you need to render filters on paths.
     */
    var buffer = new OffscreenBuffer(width, height);
    buffer.draw = callback;
    return buffer.render();
}

function filter(img, callback) {
    /* Returns a new Image object with the given pixel function applied to it.
     * The function takes an array of RGBA-values (base 255) and returns a new array.
     */
    var pixels = new Pixels(img);
    pixels.map(callback);
    pixels.update();
    return pixels.image();
}

/*##################################################################################################*/

/*--- IMAGE FILTERS | GENERATORS -------------------------------------------------------------------*/

function solid(width, height, clr) { 
    /* Returns an image with a solid fill color.
     */
    return render(function(canvas) { 
        rect(0, 0, width, height, {fill: clr || [0,0,0,0]}); 
    }, width, height);
}

/*--- IMAGE FILTERS | COLOR ------------------------------------------------------------------------*/

var LUMINANCE = [0.2125 / 255, 0.7154 / 255, 0.0721 / 255];

function invert(img) {
    /* Returns an image with inverted colors (e.g. white becomes black).
     */
    return filter(img, function(p) {
        return [255-p[0], 255-p[1], 255-p[2], p[3]];
    });
}

function colorize(img, color, bias) {
    /* Returns a colorized image.
     *  - color: a Color (or array) of RGBA-values to multiply with each image pixel.
     *  - bias : a Color (or array) of RGBA-values to add to each image pixel.
     */
    var m1 = new Color(color || [1,1,1,1]).rgba();
    var m2 = new Color(bias || [0,0,0,0]).map({base: 255});
    return filter(img, function(p) {
        return [
            p[0] * m1[0] + m2[0],
            p[1] * m1[1] + m2[1],
            p[2] * m1[2] + m2[2],
            p[3] * m1[3] + m2[3]
        ];
    });
}

// function adjust(img, {hue:0, saturation:1.0, brightness:1.0, contrast:1.0})
function adjust(img, options) {
    /* Applies color adjustment filters to the image and returns the adjusted image.
     *  - hue        : the shift in hue (1.0 is 360 degrees on the color wheel).
     *  - saturation : the intensity of the colors (0.0 is a grayscale image).
     *  - brightness : the overall lightness or darkness (0.0 is a black image).
     *  - contrast   : the difference in brightness between regions.
     */
    var pixels = new Pixels(img);
    var adjust_hue = function(pixels, m) {
        pixels.map(function(p) {
            var hsb = _rgb2hsb(p[0]/255, p[1]/255, p[2]/255);
            var rgb = _hsb2rgb(Math.clamp(Math.mod(hsb[0] + m, 1), 0, 1), hsb[1], hsb[2]);
            return [rgb[0]*255, rgb[1]*255, rgb[2]*255, p[3]]; 
        });
    }
    var adjust_saturation = function(pixels, m) {
        pixels.map(function(p) {
            var i = (0.3*p[0] + 0.59*p[1] + 0.11*p[2]) * (1-m); 
            return [p[0]*m + i, p[1]*m + i, p[2]*m + i, p[3]]; 
        });
    }
    var adjust_brightness = function(pixels, m) {
        pixels.map(function(p) {
            return [p[0] + m, p[1] + m, p[2] + m, p[3]]; 
        });
    }
    var adjust_contrast = function(pixels, m) {
        pixels.map(function(p) {
            return [(p[0]-128)*m + 128, (p[1]-128)*m + 128, (p[2]-128)*m + 128, p[3]]; 
        });
    }
    var o = options || {};
    if (o.hue !== undefined)
        adjust_hue(pixels, o.hue);
    if (o.saturation !== undefined && o.saturation != 1)
        adjust_saturation(pixels, o.saturation);
    if (o.brightness !== undefined && o.brightness != 1)
        adjust_brightness(pixels, 255 * (o.brightness-1));
    if (o.contrast !== undefined && o.contrast != 1)
        adjust_contrast(pixels, o.contrast);
    pixels.update();
    return pixels.image();
}

function desaturate(img) {
    /* Returns a grayscale version of the image.
     */
    return adjust(img, {saturation: 0});
}

function brightpass(img, threshold) {
    /* Returns a new image where pixels whose luminance fall below the threshold are black.
     */
    return filter(img, function(p) {
        return (Math.dot(p, LUMINANCE) > ((threshold || threshold == 0)? threshold : 0.5))? p : [0,0,0, p[3]];
    });    
}

function blur(img, radius) {
    /* Applies a stack blur filter to the image and returns the blurred image.
     * - radius: the radius of the blur effect in pixels (0-175).
     */
    radius = (radius === undefined)? 10 : radius;
    radius = Math.min(radius, 175);
    var buffer = new OffscreenBuffer(img._img.width, img._img.height);
    return _stackblur(img, buffer, radius);
}

/*--- IMAGE FILTERS | ALPHA COMPOSITING ------------------------------------------------------------*/
// Based on: R. Dura, 2009, http://mouaif.wordpress.com/2009/01/05/photoshop-math-with-glsl-shaders/

function composite(img1, img2, dx, dy, operator) {
    /* Returns a new Image by mixing img1 (the destination) with blend image img2 (the source).
     * The given operator is a function(pixel1, pixel2) that returns a new pixel (RGBA-array).
     * This is used to implement alpha compositing and blend modes.
     * - dx: horizontal offset (in pixels) of the blend layer.
     * - dy: vertical offset (in pixels) of the blend layer.
     */
    //var t = new Date().getTime();
    dx = dx || 0;
    dy = dy || 0;
    var pixels1 = new Pixels(img1);
    var pixels2 = new Pixels(img2);   
    for (var j=0; j < pixels1.height; j++) {
        for (var i=0; i < pixels1.width; i++) {
            if (0 <= i-dx && i-dx < pixels2.width) {
                if (0 <= j-dy && j-dy < pixels2.height) {
                    var p1 = pixels1.get(i + j * pixels1.width);
                    var p2 = pixels2.get((i-dx) + (j-dy) * pixels2.width);
                    pixels1.set(i + j * pixels1.width, operator(p1, p2));
                }
            }
        }
    }
    pixels1.update();
    //console.log(new Date().getTime() - t);
    return pixels1.image();
}

function transparent(img, alpha) {
    /* Returns a transparent version of the image.
     */
    return render(function(canvas) {
        image(img, {alpha: alpha});
    }, img.width, img.height);
}

function mask(img1, img2, dx, dy, alpha) {
    /* Applies the second image as an alpha mask to the first image.
     * The second image must be a grayscale image, where the black areas
     * make the first image transparent (e.g. punch holes in it).
     * - dx: horizontal offset (in pixels) of the blend layer.
     * - dy: vertical offset (in pixels) of the blend layer.
     */
    alpha = (alpha || alpha == 0)? alpha : 1;
    return composite(img1, img2, dx, dy, function(p1, p2) {
        p1[3] = p1[3] * p2[0]/255 * p2[3]/255 * alpha;
        return p1;
    });
}

var ADD       = "add";       // Pixels are added.
var SUBTRACT  = "subtract";  // Pixels are subtracted.
var LIGHTEN   = "lighten";   // Lightest value for each pixel.
var DARKEN    = "darken";    // Darkest value for each pixel.
var MULTIPLY  = "multiply";  // Pixels are multiplied, resulting in a darker image.
var SCREEN    = "screen";    // Pixels are inverted/multiplied/inverted, resulting in a brighter picture.
var OVERLAY   = "overlay";   // Combines multiply and screen: light parts become ligher, dark parts darker.
var HARDLIGHT = "hardlight"; // Same as overlay, but uses the blend instead of base image for luminance.
var HUE       = "hue";       // Hue from the blend image, brightness and saturation from the base image.

function blend(mode, img1, img2, dx, dy, alpha) {
    /* Applies the second image as a blend layer with the first image.
     * - dx: horizontal offset (in pixels) of the blend layer.
     * - dy: vertical offset (in pixels) of the blend layer.
     */
    alpha = (alpha || alpha == 0)? alpha : 1;
    switch(mode) {
        case ADD      : op = function(x, y) { return x + y;          }; break;
        case SUBTRACT : op = function(x, y) { return x + y - 255;    }; break;
        case LIGHTEN  : op = function(x, y) { return Math.max(x, y); }; break;
        case DARKEN   : op = function(x, y) { return Math.min(x, y); }; break;
        case MULTIPLY : op = function(x, y) { return x * y / 255;    }; break;
        case SCREEN   : op = function(x, y) { return 255 - (255-x) * (255-y) / 255; }; break;
        case OVERLAY  : op = function(x, y, luminance) { };
        case HARDLIGHT: op = function(x, y, luminance) {
            var a = 2 * x * y / 255;
            var b = 255 - 2 * (255-x) * (255-y) / 255;
            return (luminance < 0.45)? a :
                   (luminance > 0.55)? b : 
                    Math.lerp(a, b, (luminance - 0.45) * 255); }; break;
        default:
            op = function(x, y) { return 0; };
    }
    function mix(p1, p2, op, luminance) {
        var p = [0,0,0,0];
        var a = p2[3] / 255 * alpha;
        p[0] = Math.lerp(p1[0], op(p1[0], p2[0], luminance), a);
        p[1] = Math.lerp(p1[1], op(p1[1], p2[1], luminance), a);
        p[2] = Math.lerp(p1[2], op(p1[2], p2[2], luminance), a);
        p[3] = Math.lerp(p1[3], 255, a);
        return p;
    }
    // Some blend modes swap opaque blend (alpha=255) with base layer to mimic Photoshop.
    // Some blend modes use luminace (overlay & hard light).
    if (mode == ADD|| mode == SUBTRACT) {
        return composite(img1, img2, dx, dy, function(p1, p2) {
            return mix(p1, p2, op); 
        });    
    }
    if (mode == LIGHTEN || mode == DARKEN || mode == MULTIPLY || mode == SCREEN) {
        return composite(img1, img2, dx, dy, function(p1, p2) {
            return (p2[3] == 255)? mix(p2, p1, op) : mix(p1, p2, op); 
        });
    }
    if (mode == OVERLAY) {
        return composite(img1, img2, dx, dy, function(p1, p2) {
            return mix(p1, p2, op, Math.dot(p1.slice(0, 3), LUMINANCE)); 
        });
    }
    if (mode == HARDLIGHT) {
        return composite(img1, img2, dx, dy, function(p1, p2) {
            return mix(p1, p2, op, Math.dot(p2.slice(0, 3), LUMINANCE)); 
        });
    }
    if (mode == HUE) {
        return composite(img1, img2, dx, dy, function(p1, p2) {
            var p, a=p1[3];
            p1 = _rgb2hsb(p1[0], p1[1], p1[2]);
            p2 = _rgb2hsb(p2[0], p2[1], p2[2]);
            p  = _hsb2rgb(p2[0], p1[1], p1[2]); p.push(a);
            return p;
        });
    }
}

function add(img1, img2, dx, dy, alpha) {
    return blend(ADD, img1, img2, dx, dy, alpha);
}
function subtract(img1, img2, dx, dy, alpha) {
    return blend(SUBTRACT, img1, img2, dx, dy, alpha);
}
function lighten(img1, img2, dx, dy, alpha) {
    return blend(LIGHTEN, img1, img2, dx, dy, alpha);
}
function darken(img1, img2, dx, dy, alpha) {
    return blend(DARKEN, img1, img2, dx, dy, alpha);
}
function multiply(img1, img2, dx, dy, alpha) {
    return blend(MULTIPLY, img1, img2, dx, dy, alpha);
}
function screen_(img1, img2, dx, dy, alpha) {
    return blend(SCREEN, img1, img2, dx, dy, alpha);
}
function overlay(img1, img2, dx, dy, alpha) {
    return blend(OVERLAY, img1, img2, dx, dy, alpha);
}
function hardlight(img1, img2, dx, dy, alpha) {
    return blend(HARDLIGHT, img1, img2, dx, dy, alpha);
}
function hue(img1, img2, dx, dy, alpha) {
    return blend(HUE, img1, img2, dx, dy, alpha);
}

try {
    var s = screen;
    var p = [s.width, s.height, s.availWidth, s.availHeight, s.colorDepth, s.pixelDepth];
    screen = screen_;
    screen.width       = p[0];
    screen.height      = p[1];
    screen.availWidth  = p[2];
    screen.availHeight = p[3];
    screen.colorDepth  = p[4];
    screen.pixelDepth  = p[5];
} catch(e) {
}

/*--- IMAGE FILTERS | LIGHT ------------------------------------------------------------------------*/

function glow(img, intensity, radius) {
    /* Returns the image blended with a blurred version, yielding a glowing effect.
     *  - intensity: the opacity of the blur (0.0-1.0).
     *  - radius   : the blur radius. 
     */
    if (intensity === undefined) intensity = 0.5;
    var b = blur(img, radius);
    return blend(ADD, img, b, 0, 0, intensity);
}

function bloom(img, intensity, radius, threshold) {
    /* Returns the image blended with a blurred brightpass version, yielding a "magic glow" effect.
     *  - intensity: the opacity of the blur (0.0-1.0).
     *  - radius   : the blur radius.
     *  - threshold: the luminance threshold of pixels that light up.
     */
    if (intensity === undefined) intensity = 0.5;
    if (threshold === undefined) threshold = 0.3;
    var b = blur(brightpass(img, threshold), radius);
    return blend(ADD, img, b, 0, 0, intensity);
}

/*--- IMAGE FILTERS | DISTORTION -------------------------------------------------------------------*/
// Based on: L. Spagnolini, 2007, http://dem.ocracy.org/libero/photobooth/

function polar(img, x0, y0, callback) {
    /* Returns a new Image based on a polar coordinates filter.
     * The given callback is a function(distance, angle) that returns new [distance, angle].
     */
    x0 = img.width / 2 + (x0 || 0);
    y0 = img.height / 2 + (y0 || 0);
    var p1 = new Pixels(img);
    var p2 = new Pixels(img);
    for (var y1=0; y1 < p1.height; y1++) {
        for (var x1=0; x1 < p1.width; x1++) {
            var x = x1 - x0;
            var y = y1 - y0;
            var d = Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2));
            var a = Math.atan2(y, x);
            var v = callback(d, a); d=v[0]; a=v[1];
            p2.set(x1 + y1 * p1.width, p1.get(
                Math.round(x0 + Math.cos(a) * d) +
                Math.round(y0 + Math.sin(a) * d) * p1.width
            ));
        }
    }
    p2.update();
    return p2.image();
}

function bump(img, dx, dy, radius, zoom) {
    /* Returns the image with a dent distortion applied to it.
     *  - dx: horizontal offset (in pixels) of the effect.
     *  - dy: vertical offset (in pixels) of the effect.
     *  - radius: the radius of the effect in pixels.
     *  - zoom: the amount of bulge (0.0-1.0).
     */
    var m1 = radius || 0;
    var m2 = Math.clamp(zoom || 0, 0, 1);
    return polar(img, dx, dy, function(d, a) { 
        return [d * geometry.smoothstep(0, m2, d/m1), a]; 
    });
}

function dent(img, dx, dy, radius, zoom) {
    /* Returns the image with a dent distortion applied to it.
     *  - dx: horizontal offset (in pixels) of the effect.
     *  - dy: vertical offset (in pixels) of the effect.
     *  - radius: the radius of the effect in pixels.
     *  - zoom: the amount of pinch (0.0-1.0).
     */
    var m1 = radius || 0;
    var m2 = Math.clamp(zoom || 0, 0, 1);
    return polar(img, dx, dy, function(d, a) { 
        return [2 * d - d * geometry.smoothstep(0, m2, d/m1), a]; 
    });
}

function pinch(img, dx, dy, zoom) {
    /* Returns the image with a pinch distortion applied to it.
     *  - dx: horizontal offset (in pixels) of the effect.
     *  - dy: vertical offset (in pixels) of the effect.
     *  - zoom: the amount of bulge or pinch (-1.0-1.0):
     */
    var m1 = geometry.distance(0, 0, img.width, img.height);
    var m2 = Math.clamp(zoom || 0 * 0.75, -0.75, 0.75);
    return polar(img, dx, dy, function(d, a) { 
        return [d * Math.pow(m1/d, m2) * (1-m2), a]; 
    });
}

function splash(img, dx, dy, radius) {
    /* Returns the image with a light-tunnel distortion applied to it.
     *  - dx: horizontal offset (in pixels) of the effect.
     *  - dy: vertical offset (in pixels) of the effect.
     *  - radius: the radius of the unaffected area in pixels.
     */
    var m = radius || 0;
    return polar(img, dx, dy, function(d, a) { 
        return [(d > m)? m : d, a]; 
    });
}

function twirl(img, dx, dy, radius, angle) {
    /* Returns the image with a twirl distortion applied to it.
     *  - dx: horizontal offset (in pixels) of the effect.
     *  - dy: vertical offset (in pixels) of the effect.
     *  - radius: the radius of the effect in pixels.
     *  - angle: the amount of rotation in degrees.
     */
    var m1 = Math.radians(angle || 0);
    var m2 = radius || 0;
    return polar(img, dx, dy, function(d, a) { 
        return [d, a + (1 - geometry.smoothstep(-m2, m2, d)) * m1]; 
    });
}

var BUMP    = "bump";
var DENT    = "dent";
var PINCH   = "pinch";
var SPLASH  = "splash";
var TWIRL   = "twirl";

function distort(mode, img, options) {
    /* Applies the given distortion and returns a new image.
     * Optional parameters are dx, dy, radius, zoom and angle.
     */
    var o = options || {};
    switch (mode) {
        case BUMP: 
            return bump(img, o.dx, o.dy, o.radius, o.zoom);
        case DENT:
            return dent(img, o.dx, o.dy, o.radius, o.zoom);
        case PINCH:
            return pinch(img, o.dx, o.dy, o.zoom);
        case SPLASH:
            return splash(img, o.dx, o.dy, o.radius);
        case TWIRL:
            return twirl(img, o.dx, o.dy, o.radius, o.angle);
        default:
            return img;
    }
}

/*##################################################################################################*/

/*--- WIDGET ---------------------------------------------------------------------------------------*/

var STRING   = "string";
var NUMBER   = "number";
var BOOLEAN  = "boolean";
var RANGE    = "range";
var LIST     = "list";
var ARRAY    = "array";
var FUNCTION = "function";

// function widget(canvas, variable, type, {parent: null, value: null, min: 0, max: 1, step: 0.01, index: 1, callback: function(e){}})
function widget(canvas, variable, type, options) {
    /* Creates a widget linked to the given canvas.
     * The type of the widget can be STRING or NUMBER (field), BOOLEAN (checkbox),
     * RANGE (slider), LIST (dropdown list), or FUNCTION (button).
     * The value of the widget can be retrieved as canvas.variables[variable] (or canvas.variables.variable).
     * Optionally, a default value can be given. 
     * For lists, this is an array and optionally an index of the selected value.
     * For sliders, you can also set min, max and step.
     * For functions, an optional callback(event){} must be given.
     * To get at the current canvas from inside the callback, use event.target.canvas.
     * Use event.target.canvas.focus() if drawing occurs in the callback.
     */
    var v = variable;
    var o = options || {};
    if (canvas.variables[v] === undefined) {
        var parent = (o && o.parent)? o.parent : document.getElementById(canvas.id + "_widgets");
        if (!parent) {
            // No widget container is given, or exists.
            // Insert a <div id="[canvas.id]_widgets" class="widgets"> after the <canvas> element.
            parent = document.createElement("div");
            parent.id = (canvas.id + "_widgets");
            parent.className = "widgets";
            canvas.element.parentNode.insertBefore(parent, canvas.element.nextSibling);
        }
        // Create <input> element with id [canvas.id]_[variable].
        // Create an onchange() that will set the variable to the value of the widget.
        // For FUNCTION, it is an onclick() that will call options.callback(e).
        var id = canvas.id + "_" + v;
        // Fix callback event and event.target on IE8 and Safari2.
        // Function does nothing when propagate=false.
        var cb = function(e, propagate) {
            if (!e) {
                e = window.event;
            }
            if (!e && canvas.element.dispatchEvent) {
                e = new Event(); canvas.element.dispatchEvent(e)
            }
            if (e && !e.target) {
                e.target = e.srcElement || document;
            }
            if (e && e.target && e.target.nodeType === 3) {
                e.target = e.target.parentNode;
            }
            if (e && e.target && o.callback && propagate != false) {
                o.callback(e);
            }
        }
        // <input type="text" id="id" value="" />
        if (type == STRING || type == TEXT) {
            var s = "<input type='text' id='"+v+"' value='"+(o.value||"").replace(/'/g,"&#39;")+"' />";
            var f = function(e,p) { canvas.variables[this.id] = this.value; cb(e,p); };
        // <input type="text" id="id" value="0" />
        } else if (type == NUMBER) {
            var s = "<input type='text' id='"+v+"' value='"+(o.value||0)+"' />";
            var f = function(e,p) { canvas.variables[this.id] = parseFloat(this.value); cb(e,p); };
        // <input type="checkbox" id="variable" />
        } else if (type == BOOLEAN) {
            var s = "<input type='checkbox' id='"+v+"'"+((o.value==true)?" checked":"")+" />";
            var f = function(e,p) { canvas.variables[this.id] = this.checked; cb(e,p); };
        // <input type="range" id="id" value="0" min="0" max="0" step="0.01" />
        } else if (type == RANGE) {
            var s = "<input type='range' id='"+v+"' value='"+(o.value||0)+"'"
                  + " min='"+(o.min||0)+"' max='"+(o.max||1)+"' step='"+(o.step||0.01)+"' />";
            var f = function(e,p) { canvas.variables[this.id] = parseFloat(this.value); cb(e,p); };
        // <select id="id"><option value="value[i]">value[i]</option>...</select>
        } else if (type == LIST || type == ARRAY) {
            var s = "";
            var a = o.value || [""];
            for (var i=0; i < a.length; i++) {
                s += "<option "+(o.index==i?"selected ":"")+"value='"+a[i]+"'>"+a[i]+"</option>";
            }
            s = "<select id='"+v+"'>"+s+"</select>";
            f = function(e,p) { canvas.variables[this.id] = this.options[this.selectedIndex].value; cb(e,p); };
        // <button id="id" onclick="javascript:options.callback(event)">variable</button>
        } else if (type == FUNCTION) {
            var s = "<button id='"+v+"'>"+v.replace("_"," ")+"</button>";
            var f = function(e,p) { cb(e,p); };
        } else {
            throw "Variable type can be STRING, NUMBER, BOOLEAN, RANGE, LIST or FUNCTION, not '"+type+"'";
        }
        // Wrap the widget in a <span class="widget">.
        // Prepend a <label>variable</label> (except for buttons).
        // Attach the onchange() event.
        // Append to parent container.
        // Append to Canvas._widgets.
        var e = document.createElement("span");
        e.innerHTML = "<span class='label'>" + ((type == FUNCTION)? "&nbsp;" : v.replace("_"," ")) + "</span>" + s;
        e.className = "widget"
        e.lastChild.canvas = canvas;
        if (type != FUNCTION) {
            attachEvent(e.lastChild, "change", f); e.lastChild.change(null, false);
        } else {
            attachEvent(e.lastChild, "click", f);
        }
        parent.appendChild(e);
        canvas._widgets.push({
            "name": variable,
            "type": type,
         "element": e.lastChild
        });
    }
}

/*##################################################################################################*/

/*--- <SCRIPT TYPE="TEXT/CANVAS"> ------------------------------------------------------------------*/

attachEvent(window, "load", function() {
    /* Initializes <script class="canvas"> elements during window.onload().
     * Optional arguments: width, height, target="id" (<canvas> to use), loop="false" (static).
     */
    this.e = document.getElementsByTagName("script");
    for (this.i=0; this.i < this.e.length; this.i++) {
        var i = this.i; // e and i may not be set by globals in eval().
        var e = this.e;
        if (e[i].className == "canvas" || e[i].type == "text/canvas") {
            var canvas = e[i].getAttribute("target") || 
                         e[i].getAttribute("canvas");
            if (canvas) {
                // <script type="canvas" target="id">
                // Render in the <canvas> with the given id.
                canvas = document.getElementById(canvas);
            } else {
                // <script class="canvas">
                // Create a new <canvas class="canvas"> element.
                canvas = document.createElement("canvas");
                canvas.className = "canvas";
                canvas.width  = parseInt(e[i].getAttribute("width")  || 500);
                canvas.height = parseInt(e[i].getAttribute("height") || 500);
                // Add the new <canvas> to the DOM before the <script> element.
                // If the <script> is in the <head>, add it to the end of the document.
                if (e[i].parentNode == document.getElementsByTagName("head")[0]) {
                    document.appendChild(canvas);
                } else {
                    e[i].parentNode.insertBefore(canvas, e[i]);
                }
            }
            var async = function(canvas, e, i) { setTimeout(function() {
                // Evaluate the script and bind setup() and draw() to the canvas.
                var setup = function(){};
                var draw  = function(){};
                var stop  = function(){};
                eval(e[i].innerHTML);
                canvas = new Canvas(canvas);
                canvas.draw  = draw;
                canvas.setup = setup;
                canvas.stop  = function() { 
                    stop(this); this._stop();
                }
                // <script class="canvas" loop="false"> renders a single frame.
                if (e[i].getAttribute("loop") == "false") {
                    canvas.step();
                } else {
                    canvas.run();
                }
            }, 0); };
            async(canvas, e, i);
        }
    }
});

/*##################################################################################################*/

/*--- FAST STACK BLUR ------------------------------------------------------------------------------*/
// Mario Klingemann (2010), http://www.quasimondo.com/StackBlurForCanvas/StackBlur.js

var _stackblur_mul=[512,512,456,512,328,456,335,512,405,328,271,456,388,335,292,512,454,405,364,328,298,271,496,456,420,388,360,335,312,292,273,512,482,454,428,405,383,364,345,328,312,298,284,271,259,496,475,456,437,420,404,388,374,360,347,335,323,312,302,292,282,273,265,512,497,482,468,454,441,428,417,405,394,383,373,364,354,345,337,328,320,312,305,298,291,284,278,271,265,259,507,496,485,475,465,456,446,437,428,420,412,404,396,388,381,374,367,360,354,347,341,335,329,323,318,312,307,302,297,292,287,282,278,273,269,265,261,512,505,497,489,482,475,468,461,454,447,441,435,428,422,417,411,405,399,394,389,383,378,373,368,364,359,354,350,345,341,337,332,328,324,320,316,312,309,305,301,298,294,291,287,284,281,278,274,271,268,265,262,259,257,507,501,496,491,485,480,475,470,465,460,456,451,446,442,437,433,428,424,420,416,412,408,404,400,396,392,388,385,381,377,374,370,367,363,360,357,354,350,347,344,341,338,335,332,329,326,323,320,318,315,312,310,307,304,302,299,297,294,292,289,287,285,282,280,278,275,273,271,269,267,265,263,261,259];
var _stackblur_shg=[9,11,12,13,13,14,14,15,15,15,15,16,16,16,16,17,17,17,17,17,17,17,18,18,18,18,18,18,18,18,18,19,19,19,19,19,19,19,19,19,19,19,19,19,19,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,20,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,21,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,22,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,23,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24,24];

function _stackblur(img, buffer, radius) {

function BlurStack(){this.r=0;this.g=0;this.b=0;this.a=0;this.next=null}function stackBlurCanvasRGBA(a,b,c,d,e,f){if(isNaN(f)||f<1)return;f|=0;var g=a.element;var h=g.getContext("2d");var i;i=h.getImageData(b,c,d,e);var k=i.data;var l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I;var J=f+f+1;var K=d<<2;var L=d-1;var M=e-1;var N=f+1;var O=N*(N+1)/2;var P=new BlurStack;var Q=P;for(n=1;n<J;n++){Q=Q.next=new BlurStack;if(n==N)var R=Q}Q.next=P;var S=null;var T=null;r=q=0;var U=_stackblur_mul[f];var V=_stackblur_shg[f];for(m=0;m<e;m++){A=B=C=D=s=t=u=v=0;w=N*(E=k[q]);x=N*(F=k[q+1]);y=N*(G=k[q+2]);z=N*(H=k[q+3]);s+=O*E;t+=O*F;u+=O*G;v+=O*H;Q=P;for(n=0;n<N;n++){Q.r=E;Q.g=F;Q.b=G;Q.a=H;Q=Q.next}for(n=1;n<N;n++){o=q+((L<n?L:n)<<2);s+=(Q.r=E=k[o])*(I=N-n);t+=(Q.g=F=k[o+1])*I;u+=(Q.b=G=k[o+2])*I;v+=(Q.a=H=k[o+3])*I;A+=E;B+=F;C+=G;D+=H;Q=Q.next}S=P;T=R;for(l=0;l<d;l++){k[q+3]=H=v*U>>V;if(H!=0){H=255/H;k[q]=(s*U>>V)*H;k[q+1]=(t*U>>V)*H;k[q+2]=(u*U>>V)*H}else{k[q]=k[q+1]=k[q+2]=0}s-=w;t-=x;u-=y;v-=z;w-=S.r;x-=S.g;y-=S.b;z-=S.a;o=r+((o=l+f+1)<L?o:L)<<2;A+=S.r=k[o];B+=S.g=k[o+1];C+=S.b=k[o+2];D+=S.a=k[o+3];s+=A;t+=B;u+=C;v+=D;S=S.next;w+=E=T.r;x+=F=T.g;y+=G=T.b;z+=H=T.a;A-=E;B-=F;C-=G;D-=H;T=T.next;q+=4}r+=d}for(l=0;l<d;l++){B=C=D=A=t=u=v=s=0;q=l<<2;w=N*(E=k[q]);x=N*(F=k[q+1]);y=N*(G=k[q+2]);z=N*(H=k[q+3]);s+=O*E;t+=O*F;u+=O*G;v+=O*H;Q=P;for(n=0;n<N;n++){Q.r=E;Q.g=F;Q.b=G;Q.a=H;Q=Q.next}p=d;for(n=1;n<=f;n++){q=p+l<<2;s+=(Q.r=E=k[q])*(I=N-n);t+=(Q.g=F=k[q+1])*I;u+=(Q.b=G=k[q+2])*I;v+=(Q.a=H=k[q+3])*I;A+=E;B+=F;C+=G;D+=H;Q=Q.next;if(n<M){p+=d}}q=l;S=P;T=R;for(m=0;m<e;m++){o=q<<2;k[o+3]=H=v*U>>V;if(H>0){H=255/H;k[o]=(s*U>>V)*H;k[o+1]=(t*U>>V)*H;k[o+2]=(u*U>>V)*H}else{k[o]=k[o+1]=k[o+2]=0}s-=w;t-=x;u-=y;v-=z;w-=S.r;x-=S.g;y-=S.b;z-=S.a;o=l+((o=m+N)<M?o:M)*d<<2;s+=A+=S.r=k[o];t+=B+=S.g=k[o+1];u+=C+=S.b=k[o+2];v+=D+=S.a=k[o+3];S=S.next;w+=E=T.r;x+=F=T.g;y+=G=T.b;z+=H=T.a;A-=E;B-=F;C-=G;D-=H;T=T.next;q+=d}}h.putImageData(i,b,c)}function stackBlurImage(a,b,c,d){var e=a._img;var f=e.width;var g=e.height;var h=b.element;h.style.width=f+"px";h.style.height=g+"px";h.width=f;h.height=g;var i=h.getContext("2d");i.clearRect(0,0,f,g);i.drawImage(e,0,0);if(isNaN(c)||c<1)return;if(d)stackBlurCanvasRGBA(b,0,0,f,g,c);else stackBlurCanvasRGB(b,0,0,f,g,c)}

stackBlurImage(img, buffer, radius, true);
return buffer.image();
};

/*##################################################################################################*/

/*--- EXPLORER CANVAS ------------------------------------------------------------------------------*/
// http://code.google.com/p/explorercanvas/
// Fallback using VML on IE7 and IE8.

function _IEVersion() {
    if (navigator.appName == "Microsoft Internet Explorer") {
        if (new RegExp("MSIE ([0-9]{1,}[\.0-9]{0,})").exec(navigator.userAgent) != null) {
            return parseFloat(RegExp.$1);
        }
    }
}

var ie = _IEVersion();
if (ie && ie < 9) { 
    
// Copyright 2006 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

document.createElement("canvas").getContext||(function(){var s=Math,j=s.round,F=s.sin,G=s.cos,V=s.abs,W=s.sqrt,k=10,v=k/2;function X(){return this.context_||(this.context_=new H(this))}var L=Array.prototype.slice;function Y(b,a){var c=L.call(arguments,2);return function(){return b.apply(a,c.concat(L.call(arguments)))}}var M={init:function(b){if(/MSIE/.test(navigator.userAgent)&&!window.opera){var a=b||document;a.createElement("canvas");a.attachEvent("onreadystatechange",Y(this.init_,this,a))}},init_:function(b){b.namespaces.g_vml_||
b.namespaces.add("g_vml_","urn:schemas-microsoft-com:vml","#default#VML");b.namespaces.g_o_||b.namespaces.add("g_o_","urn:schemas-microsoft-com:office:office","#default#VML");if(!b.styleSheets.ex_canvas_){var a=b.createStyleSheet();a.owningElement.id="ex_canvas_";a.cssText="canvas{display:inline-block;overflow:hidden;text-align:left;width:300px;height:150px}g_vml_\\:*{behavior:url(#default#VML)}g_o_\\:*{behavior:url(#default#VML)}"}var c=b.getElementsByTagName("canvas"),d=0;for(;d<c.length;d++)this.initElement(c[d])},
initElement:function(b){if(!b.getContext){b.getContext=X;b.innerHTML="";b.attachEvent("onpropertychange",Z);b.attachEvent("onresize",$);var a=b.attributes;if(a.width&&a.width.specified)b.style.width=a.width.nodeValue.replace("px","")+"px";else b.width=b.clientWidth;if(a.height&&a.height.specified)b.style.height=a.height.nodeValue.replace("px","")+"px";else b.height=b.clientHeight}return b}};function Z(b){var a=b.srcElement;switch(b.propertyName){case "width":a.style.width=a.attributes.width.nodeValue.replace("px","")+"px";a.getContext().clearRect();
break;case "height":a.style.height=a.attributes.height.nodeValue.replace("px","")+"px";a.getContext().clearRect();break}}function $(b){var a=b.srcElement;if(a.firstChild){a.firstChild.style.width=a.clientWidth+"px";a.firstChild.style.height=a.clientHeight+"px"}}M.init();var N=[],B=0;for(;B<16;B++){var C=0;for(;C<16;C++)N[B*16+C]=B.toString(16)+C.toString(16)}function I(){return[[1,0,0],[0,1,0],[0,0,1]]}function y(b,a){var c=I(),d=0;for(;d<3;d++){var f=0;for(;f<3;f++){var h=0,g=0;for(;g<3;g++)h+=b[d][g]*a[g][f];c[d][f]=
h}}return c}function O(b,a){a.fillStyle=b.fillStyle;a.lineCap=b.lineCap;a.lineJoin=b.lineJoin;a.lineWidth=b.lineWidth;a.miterLimit=b.miterLimit;a.shadowBlur=b.shadowBlur;a.shadowColor=b.shadowColor;a.shadowOffsetX=b.shadowOffsetX;a.shadowOffsetY=b.shadowOffsetY;a.strokeStyle=b.strokeStyle;a.globalAlpha=b.globalAlpha;a.arcScaleX_=b.arcScaleX_;a.arcScaleY_=b.arcScaleY_;a.lineScale_=b.lineScale_}function P(b){var a,c=1;b=String(b);if(b.substring(0,3)=="rgb"){var d=b.indexOf("(",3),f=b.indexOf(")",d+
1),h=b.substring(d+1,f).split(",");a="#";var g=0;for(;g<3;g++)a+=N[Number(h[g])];if(h.length==4&&b.substr(3,1)=="a")c=h[3]}else a=b;return{color:a,alpha:c}}function aa(b){switch(b){case "butt":return"flat";case "round":return"round";case "square":default:return"square"}}function H(b){this.m_=I();this.mStack_=[];this.aStack_=[];this.currentPath_=[];this.fillStyle=this.strokeStyle="#000";this.lineWidth=1;this.lineJoin="miter";this.lineCap="butt";this.miterLimit=k*1;this.globalAlpha=1;this.canvas=b;
var a=b.ownerDocument.createElement("div");a.style.width=b.clientWidth+"px";a.style.height=b.clientHeight+"px";a.style.overflow="hidden";a.style.position="absolute";b.appendChild(a);this.element_=a;this.lineScale_=this.arcScaleY_=this.arcScaleX_=1}var i=H.prototype;i.clearRect=function(){this.element_.innerHTML=""};i.beginPath=function(){this.currentPath_=[]};i.moveTo=function(b,a){var c=this.getCoords_(b,a);this.currentPath_.push({type:"moveTo",x:c.x,y:c.y});this.currentX_=c.x;this.currentY_=c.y};
i.lineTo=function(b,a){var c=this.getCoords_(b,a);this.currentPath_.push({type:"lineTo",x:c.x,y:c.y});this.currentX_=c.x;this.currentY_=c.y};i.bezierCurveTo=function(b,a,c,d,f,h){var g=this.getCoords_(f,h),l=this.getCoords_(b,a),e=this.getCoords_(c,d);Q(this,l,e,g)};function Q(b,a,c,d){b.currentPath_.push({type:"bezierCurveTo",cp1x:a.x,cp1y:a.y,cp2x:c.x,cp2y:c.y,x:d.x,y:d.y});b.currentX_=d.x;b.currentY_=d.y}i.quadraticCurveTo=function(b,a,c,d){var f=this.getCoords_(b,a),h=this.getCoords_(c,d),g={x:this.currentX_+
0.6666666666666666*(f.x-this.currentX_),y:this.currentY_+0.6666666666666666*(f.y-this.currentY_)};Q(this,g,{x:g.x+(h.x-this.currentX_)/3,y:g.y+(h.y-this.currentY_)/3},h)};i.arc=function(b,a,c,d,f,h){c*=k;var g=h?"at":"wa",l=b+G(d)*c-v,e=a+F(d)*c-v,m=b+G(f)*c-v,r=a+F(f)*c-v;if(l==m&&!h)l+=0.125;var n=this.getCoords_(b,a),o=this.getCoords_(l,e),q=this.getCoords_(m,r);this.currentPath_.push({type:g,x:n.x,y:n.y,radius:c,xStart:o.x,yStart:o.y,xEnd:q.x,yEnd:q.y})};i.rect=function(b,a,c,d){this.moveTo(b,
a);this.lineTo(b+c,a);this.lineTo(b+c,a+d);this.lineTo(b,a+d);this.closePath()};i.strokeRect=function(b,a,c,d){var f=this.currentPath_;this.beginPath();this.moveTo(b,a);this.lineTo(b+c,a);this.lineTo(b+c,a+d);this.lineTo(b,a+d);this.closePath();this.stroke();this.currentPath_=f};i.fillRect=function(b,a,c,d){var f=this.currentPath_;this.beginPath();this.moveTo(b,a);this.lineTo(b+c,a);this.lineTo(b+c,a+d);this.lineTo(b,a+d);this.closePath();this.fill();this.currentPath_=f};i.createLinearGradient=function(b,
a,c,d){var f=new D("gradient");f.x0_=b;f.y0_=a;f.x1_=c;f.y1_=d;return f};i.createRadialGradient=function(b,a,c,d,f,h){var g=new D("gradientradial");g.x0_=b;g.y0_=a;g.r0_=c;g.x1_=d;g.y1_=f;g.r1_=h;return g};i.drawImage=function(b){var a,c,d,f,h,g,l,e,m=b.runtimeStyle.width,r=b.runtimeStyle.height;b.runtimeStyle.width="auto";b.runtimeStyle.height="auto";var n=b.width,o=b.height;b.runtimeStyle.width=m;b.runtimeStyle.height=r;if(arguments.length==3){a=arguments[1];c=arguments[2];h=g=0;l=d=n;e=f=o}else if(arguments.length==
5){a=arguments[1];c=arguments[2];d=arguments[3];f=arguments[4];h=g=0;l=n;e=o}else if(arguments.length==9){h=arguments[1];g=arguments[2];l=arguments[3];e=arguments[4];a=arguments[5];c=arguments[6];d=arguments[7];f=arguments[8]}else throw Error("Invalid number of arguments");var q=this.getCoords_(a,c),t=[];t.push(" <g_vml_:group",' coordsize="',k*10,",",k*10,'"',' coordorigin="0,0"',' style="width:',10,"px;height:",10,"px;position:absolute;");if(this.m_[0][0]!=1||this.m_[0][1]){var E=[];E.push("M11=",
this.m_[0][0],",","M12=",this.m_[1][0],",","M21=",this.m_[0][1],",","M22=",this.m_[1][1],",","Dx=",j(q.x/k),",","Dy=",j(q.y/k),"");var p=q,z=this.getCoords_(a+d,c),w=this.getCoords_(a,c+f),x=this.getCoords_(a+d,c+f);p.x=s.max(p.x,z.x,w.x,x.x);p.y=s.max(p.y,z.y,w.y,x.y);t.push("padding:0 ",j(p.x/k),"px ",j(p.y/k),"px 0;filter:progid:DXImageTransform.Microsoft.Matrix(",E.join(""),", sizingmethod='clip');")}else t.push("top:",j(q.y/k),"px;left:",j(q.x/k),"px;");t.push(' ">','<g_vml_:image src="',b.src,
'"',' style="width:',k*d,"px;"," height:",k*f,'px;"',' cropleft="',h/n,'"',' croptop="',g/o,'"',' cropright="',(n-h-l)/n,'"',' cropbottom="',(o-g-e)/o,'"'," />","</g_vml_:group>");this.element_.insertAdjacentHTML("BeforeEnd",t.join(""))};i.stroke=function(b){var a=[],c=P(b?this.fillStyle:this.strokeStyle),d=c.color,f=c.alpha*this.globalAlpha;a.push("<g_vml_:shape",' filled="',!!b,'"',' style="position:absolute;width:',10,"px;height:",10,'px;"',' coordorigin="0 0" coordsize="',k*10," ",k*10,'"',' stroked="',
!b,'"',' path="');var h={x:null,y:null},g={x:null,y:null},l=0;for(;l<this.currentPath_.length;l++){var e=this.currentPath_[l];switch(e.type){case "moveTo":a.push(" m ",j(e.x),",",j(e.y));break;case "lineTo":a.push(" l ",j(e.x),",",j(e.y));break;case "close":a.push(" x ");e=null;break;case "bezierCurveTo":a.push(" c ",j(e.cp1x),",",j(e.cp1y),",",j(e.cp2x),",",j(e.cp2y),",",j(e.x),",",j(e.y));break;case "at":case "wa":a.push(" ",e.type," ",j(e.x-this.arcScaleX_*e.radius),",",j(e.y-this.arcScaleY_*e.radius),
" ",j(e.x+this.arcScaleX_*e.radius),",",j(e.y+this.arcScaleY_*e.radius)," ",j(e.xStart),",",j(e.yStart)," ",j(e.xEnd),",",j(e.yEnd));break}if(e){if(h.x==null||e.x<h.x)h.x=e.x;if(g.x==null||e.x>g.x)g.x=e.x;if(h.y==null||e.y<h.y)h.y=e.y;if(g.y==null||e.y>g.y)g.y=e.y}}a.push(' ">');if(b)if(typeof this.fillStyle=="object"){var m=this.fillStyle,r=0,n={x:0,y:0},o=0,q=1;if(m.type_=="gradient"){var t=m.x1_/this.arcScaleX_,E=m.y1_/this.arcScaleY_,p=this.getCoords_(m.x0_/this.arcScaleX_,m.y0_/this.arcScaleY_),
z=this.getCoords_(t,E);r=Math.atan2(z.x-p.x,z.y-p.y)*180/Math.PI;if(r<0)r+=360;if(r<1.0E-6)r=0}else{var p=this.getCoords_(m.x0_,m.y0_),w=g.x-h.x,x=g.y-h.y;n={x:(p.x-h.x)/w,y:(p.y-h.y)/x};w/=this.arcScaleX_*k;x/=this.arcScaleY_*k;var R=s.max(w,x);o=2*m.r0_/R;q=2*m.r1_/R-o}var u=m.colors_;u.sort(function(ba,ca){return ba.offset-ca.offset});var J=u.length,da=u[0].color,ea=u[J-1].color,fa=u[0].alpha*this.globalAlpha,ga=u[J-1].alpha*this.globalAlpha,S=[],l=0;for(;l<J;l++){var T=u[l];S.push(T.offset*q+
o+" "+T.color)}a.push('<g_vml_:fill type="',m.type_,'"',' method="none" focus="100%"',' color="',da,'"',' color2="',ea,'"',' colors="',S.join(","),'"',' opacity="',ga,'"',' g_o_:opacity2="',fa,'"',' angle="',r,'"',' focusposition="',n.x,",",n.y,'" />')}else a.push('<g_vml_:fill color="',d,'" opacity="',f,'" />');else{var K=this.lineScale_*this.lineWidth;if(K<1)f*=K;a.push("<g_vml_:stroke",' opacity="',f,'"',' joinstyle="',this.lineJoin,'"',' miterlimit="',this.miterLimit,'"',' endcap="',aa(this.lineCap),
'"',' weight="',K,'px"',' color="',d,'" />')}a.push("</g_vml_:shape>");this.element_.insertAdjacentHTML("beforeEnd",a.join(""))};i.fill=function(){this.stroke(true)};i.closePath=function(){this.currentPath_.push({type:"close"})};i.getCoords_=function(b,a){var c=this.m_;return{x:k*(b*c[0][0]+a*c[1][0]+c[2][0])-v,y:k*(b*c[0][1]+a*c[1][1]+c[2][1])-v}};i.save=function(){var b={};O(this,b);this.aStack_.push(b);this.mStack_.push(this.m_);this.m_=y(I(),this.m_)};i.restore=function(){O(this.aStack_.pop(),
this);this.m_=this.mStack_.pop()};function ha(b){var a=0;for(;a<3;a++){var c=0;for(;c<2;c++)if(!isFinite(b[a][c])||isNaN(b[a][c]))return false}return true}function A(b,a,c){if(!!ha(a)){b.m_=a;if(c)b.lineScale_=W(V(a[0][0]*a[1][1]-a[0][1]*a[1][0]))}}i.translate=function(b,a){A(this,y([[1,0,0],[0,1,0],[b,a,1]],this.m_),false)};i.rotate=function(b){var a=G(b),c=F(b);A(this,y([[a,c,0],[-c,a,0],[0,0,1]],this.m_),false)};i.scale=function(b,a){this.arcScaleX_*=b;this.arcScaleY_*=a;A(this,y([[b,0,0],[0,a,
0],[0,0,1]],this.m_),true)};i.transform=function(b,a,c,d,f,h){A(this,y([[b,a,0],[c,d,0],[f,h,1]],this.m_),true)};i.setTransform=function(b,a,c,d,f,h){A(this,[[b,a,0],[c,d,0],[f,h,1]],true)};i.clip=function(){};i.arcTo=function(){};i.createPattern=function(){return new U};function D(b){this.type_=b;this.r1_=this.y1_=this.x1_=this.r0_=this.y0_=this.x0_=0;this.colors_=[]}D.prototype.addColorStop=function(b,a){a=P(a);this.colors_.push({offset:b,color:a.color,alpha:a.alpha})};function U(){}G_vmlCanvasManager=
M;CanvasRenderingContext2D=H;CanvasGradient=D;CanvasPattern=U})();

}
