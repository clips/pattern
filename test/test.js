function assert(expression) {
    /* Throws AssertException if the given expression evaluates to false.
     */
	if (!expression) throw "AssertException";
}

function TestCase() {
    /* TestCase objects have a setUp() and a tearDown() method, 
     * called before and after each test respectively.
     * Tests in a TestCase have method names starting with "test".
     */ 
    this.setUp = function() {
        return;
    };
    this.tearDown = function() {
        return;
    };
    this.testMethod = function() {
        assert(true == false);
    };	
}

function run(tests) {
    /* Executes each method which name starts with "test",
     * for each TestCase object in the given array.
     * Throws AssertException if the method fails.
     */
    for (var i=0; i < tests.length; i++) {
        for (var method in tests[i]) {
            if (method.substring(0,4) == "test") {
                tests[i].setUp();
                try {
                    tests[i][method]();
                } catch(e) {
                    console.error(e + " in " + method + "()");
                }
                tests[i].tearDown();
            }
        }
    }
}