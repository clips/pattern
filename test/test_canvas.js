var test_canvas = {
    
    //----------------------------------------------------------------------------------------------
    // Unit tests for the canvas.js module (see also test.html).

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
    	this.test_find = function() {
    		assert(Array.find([1,2,3], function(x) { return x==2; }) == 1);
    		console.log("Array.sum()");
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
    },

    //----------------------------------------------------------------------------------------------
    
    suite: function() {
        return [
            new test_canvas.TestArray(),
            new test_canvas.TestColor(),
        ];
    }
    
}