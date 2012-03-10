/**
 * SyntaxHighlighter
 * http://alexgorbatchev.com/SyntaxHighlighter
 *
 * SyntaxHighlighter is donationware. If you are using it, please donate.
 * http://alexgorbatchev.com/SyntaxHighlighter/donate.html
 *
 * @version
 * 3.0.83 (July 02 2010)
 * 
 * @copyright
 * Copyright (C) 2004-2010 Alex Gorbatchev.
 *
 * @license
 * Dual licensed under the MIT and GPL licenses.
 */
;(function()
{
	// CommonJS
	typeof(require) != 'undefined' ? SyntaxHighlighter = require('shCore').SyntaxHighlighter : null;

	function Brush()
	{
		var keywords1 =	'break case catch continue ' +
						'default delete do else  ' +
						'for function if in instanceof ' +
						'new return switch ' +
						'throw try typeof var while with'
						;
						
		var keywords2 =	'false true null super this';
		
		var keywords3 =	'alert back blur close confirm focus forward home' +
						'name navigate onblur onerror onfocus onload onmove' +
						'onresize onunload open print prompt scroll status stop';

		var r = SyntaxHighlighter.regexLib;
		
		this.regexList = [
			{ regex: r.multiLineDoubleQuotedString,					css: 'string' },			// double quoted strings
			{ regex: r.multiLineSingleQuotedString,					css: 'string' },			// single quoted strings
			{ regex: r.singleLineCComments,							css: 'comments1' },			// one line comments
			{ regex: r.multiLineCComments,							css: 'comments2' },			// multiline comments
			{ regex: /\s*#.*/gm,									css: 'preprocessor' },		// preprocessor tags like #region and #endregion
			{ regex: /function ([^\()]+)\(/g, func: function(match, r) { 
				return [
				    new SyntaxHighlighter.Match("function ", match.index, "keyword1"), 
				    new SyntaxHighlighter.Match(match[1], match.index+9, "name")
				]; } },
			{ regex: new RegExp(this.getKeywords(keywords1), 'gm'),	css: 'keyword1' },			// keywords 1
			{ regex: new RegExp(this.getKeywords(keywords2), 'gm'),	css: 'keyword2' },			// keywords 2
			{ regex: new RegExp(this.getKeywords(keywords3), 'gm'),	css: 'keyword3' }			// keywords 3
			];
	
		this.forHtmlScript(r.scriptScriptTags);
	};

	Brush.prototype	= new SyntaxHighlighter.Highlighter();
	Brush.aliases	= ['js', 'jscript', 'javascript'];

	SyntaxHighlighter.brushes.JScript = Brush;

	// CommonJS
	typeof(exports) != 'undefined' ? exports.Brush = Brush : null;
})();
