var test_canvas = {
    
    //----------------------------------------------------------------------------------------------
    // Unit tests for the canvas.js module (see also test.html).

    TestUtility: function() {
        this.setUp = function() {
            return;
        };
        this.tearDown = function() {
            return;
        };
        this.test_closure = function() {
            var o = {"k": "v"};
            var m = function() { return this.k };
            assert(Function.closure(o, m)() == "v");
            console.log("Function.closure()");
        };
    },

    //----------------------------------------------------------------------------------------------
    
    TestGeometry: function() {
        this.setUp = function() {
            return;
        };
        this.tearDown = function() {
            return;
        };
        this.test_round = function() {
            assert(Math.round(3.445, 2) == 3.45);
            console.log("Math.round()");
        };
        this.test_sign = function() {
            assert(Math.sign(+10) == +1);
            assert(Math.sign(-10) == -1);
            console.log("Math.sign()");
        };
        this.test_degrees = function() {
            assert(Math.degrees(Math.PI) == 180);
            console.log("Math.round()");
        };
        this.test_radians = function() {
            assert(Math.radians(180) == Math.PI);
            console.log("Math.round()");
        };
        this.test_radians = function() {
            assert(Math.radians(180) == Math.PI);
            console.log("Math.round()");
        };
        this.test_clamp = function() {
            assert(Math.clamp(+10, 0, 1) == 1);
            assert(Math.clamp(-10, 0, 1) == 0);
            console.log("Math.clamp()");
        };
        this.test_dot = function() {
            assert(Math.dot([1,2,3], [4,5,6]) == 32);
            console.log("Math.dot()");
        };
        this.test_point = function() {
            assert(new Point(1,2).copy().x == 1);
            assert(new Point(1,2).copy().y == 2);
            console.log("Point()");
        };
        this.test_angle = function() {
            assert(geometry.angle(0, 0, 10, 10) == 45);
            console.log("geometry.angle()");
        };
        this.test_distance = function() {
            assert(geometry.distance(0, 0, 10, 10) == Math.sqrt(100+100));
            console.log("geometry.distance()");
        };
        this.test_coordinates = function() {
            var pt = geometry.coordinates(0, 0, Math.sqrt(200), 45);
            assert(Math.round(pt.x) == 10);
            assert(Math.round(pt.y) == 10);
            console.log("geometry.coordinates()");
        };
        this.test_rotate = function() {
            var pt = geometry.rotate(10, 10, 0, 0, 180);
            assert(Math.round(pt.x) == -10);
            assert(Math.round(pt.y) == -10);
            console.log("geometry.rotate()");
        };
        this.test_reflect = function() {
            var pt = geometry.reflect(0, 0, 10, 10, 2.0, 180);
            assert(Math.round(pt.x) == -20);
            assert(Math.round(pt.y) == -20);
            console.log("geometry.reflect()");
        };
        this.test_lerp = function() {
            assert(geometry.lerp(100, 200, 0.5) == 150);
            console.log("geometry.lerp()");
        };
        this.test_smoothstep = function() {
            assert(geometry.smoothstep(0, 1, 0.00) == 0);
            assert(geometry.smoothstep(0, 1, 0.50) == 0.5);
            assert(geometry.smoothstep(0, 1, 0.75) == 0.84375);
            console.log("geometry.lerp()");
        };
    },
    
    //----------------------------------------------------------------------------------------------
    
    TestArray: function() {
        this.setUp = function() {
            return;
        };
        this.tearDown = function() {
            return;
        };
        this.test_min = function() {
            assert(Array.min([1,2,3]) == 1);
            console.log("Array.min()");
        };
        this.test_max = function() {
            assert(Array.max([1,2,3]) == 3);
            console.log("Array.max()");
        };
        this.test_sum = function() {
            assert(Array.sum([1,2,3]) == 6);
            console.log("Array.sum()");
        };
        this.test_contains = function() {
            assert(Array.contains([1,2,3], 0) == false);
            assert(Array.contains([1,2,3], 1) == true);
            console.log("Array.contains()");
        };
        this.test_find = function() {
            assert(Array.find([1,2,3], function(x) { return x==2; }) == 1);
            console.log("Array.find()");
        };
        this.test_map = function() {
            assert(Array.eq(Array.map([1,2,3], function(x) { return x-1; }), [0,1,2]));
            console.log("Array.map()");
        };
        this.test_filter = function() {
            assert(Array.eq(Array.filter([1,2,3], function(x) { return x<3; }), [1,2]));
            console.log("Array.filter()");
        };
        this.test_sorted = function() {
            assert(Array.eq(Array.sorted([2,3,1]), [1,2,3]));
            console.log("Array.sorted()");
        };
        this.test_reversed = function() {
            assert(Array.eq(Array.reversed([1,2,3]), [3,2,1]));
            console.log("Array.reversed()");
        };
        this.test_range = function() {
            assert(Array.eq(Array.range(3), [0,1,2]));
            assert(Array.eq(Array.range(1,4), [1,2,3]));
            console.log("Array.range()");
        };
    },
    
    //----------------------------------------------------------------------------------------------
    
    TestColor: function() {
        this.setUp = function() {
            return;
        };
        this.tearDown = function() {
            return;
        };
        this.test_color = function() {
            assert(Array.eq(new Color().rgba(), [0,0,0,0]));
            assert(Array.eq(new Color(0).rgba(), [0,0,0,1]));
            assert(Array.eq(new Color(1).rgba(), [1,1,1,1]));
            assert(Array.eq(new Color(0,0).rgba(), [0,0,0,0]));
            assert(Array.eq(new Color(0,0,0.5).rgba(), [0,0,0.5,1]));
            assert(Array.eq(new Color(1,1,1,1).rgba(), [1,1,1,1]));
            assert(Array.eq(new Color([1,0,0,1]).rgba(), [1,0,0,1]));
            assert(Array.eq(new Color([1,0,0,0]).rgba(), [1,0,0,0]));
            assert(Array.eq(new Color(255,255,0,0, {base:255}).rgba(), [1,1,0,0]));
            assert(Array.eq(new Color(1,1,0.5,0, {colorspace:HSB}).rgba(), [0.5,0,0,0]));
            assert(Array.eq(new Color(new Color(0)).rgba(), [0,0,0,1]));
            console.log("Color()");
        };
        this.test_rgb = function() {
            assert(Array.eq(new Color(1,0.5,0).rgb(), [1,0.5,0]));
            console.log("Color.rgb()")
        };
        this.test_rgba = function() {
            assert(Array.eq(new Color(1,0.5,0,0).rgba(), [1,0.5,0,0]));
            console.log("Color.rgba()")
        };
        this.test_map = function() {
            assert(Array.eq(new Color(1,0,0).map({base:255}), [255,0,0,255]));
            assert(Array.eq(new Color(1,0,0).map({colorspace:HSB}), [0,1,1,1]));
            console.log("Color.map()")
        };
        this.test_rotate = function() {
            var rgba = new Color(1,0,0).rotate(180).rgba();
            assert(Math.round(rgba[0], 1) == 0.0);
            assert(Math.round(rgba[1], 1) == 1.0);
            assert(Math.round(rgba[2], 1) == 0.3);
            assert(Math.round(rgba[3], 1) == 1.0);
            console.log("Color.rotate()")
        }
        this.test_rgb2hex = function() {
            assert(_rgb2hex(0, 0, 0) === '#000000');
            assert(_rgb2hex(1, 1, 1) === '#FFFFFF');
            assert(_rgb2hex(0.01, 0.5, 0.99) === '#0380FC');
            console.log("_rgb2hex()")
        }
    },

    //----------------------------------------------------------------------------------------------
    
    suite: function() {
        return [
            new test_canvas.TestUtility(),
            new test_canvas.TestArray(),
            new test_canvas.TestGeometry(),
            new test_canvas.TestColor(),
        ];
    }
    
}
