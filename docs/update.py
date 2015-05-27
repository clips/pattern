#### DOCUMENTATION GENERATOR ##########################################################################
# Keeps the offline documention in synch with the online documentation.
# Simply run "python update.py" to generate the latest version.

import os, sys; sys.path.insert(0, os.path.join(".."))
import codecs
import re

from pattern.web import URL, Document, strip_javascript, strip_between

url = "http://www.clips.ua.ac.be/pages/"

#--- HTML TEMPLATE -----------------------------------------------------------------------------------
# Use a simplified HTML template based on the online documentation.

template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
    <title>%s</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <link type="text/css" rel="stylesheet" href="../clips.css" />
    <style>
        /* Small fixes because we omit the online layout.css. */
        h3 { line-height: 1.3em; }
        #page { margin-left: auto; margin-right: auto; }
        #header, #header-inner { height: 175px; }
        #header { border-bottom: 1px solid #C6D4DD;  }
        table { border-collapse: collapse; }
        #checksum { display: none; }
    </style>
    <link href="../js/shCore.css" rel="stylesheet" type="text/css" />
    <link href="../js/shThemeDefault.css" rel="stylesheet" type="text/css" />
    <script language="javascript" src="../js/shCore.js"></script>
    <script language="javascript" src="../js/shBrushXml.js"></script>
    <script language="javascript" src="../js/shBrushJScript.js"></script>
    <script language="javascript" src="../js/shBrushPython.js"></script>
</head>
<body class="node-type-page one-sidebar sidebar-right section-pages">
    <div id="page">
    <div id="page-inner">
    <div id="header"><div id="header-inner"></div></div>
    <div id="content">
    <div id="content-inner">
    <div class="node node-type-page"
        <div class="node-inner">
        <div class="breadcrumb">View online at: <a href="%s" class="noexternal" target="_blank">%s</a></div>
        <h1>%s</h1>
        <!-- Parsed from the online documentation. -->
        %s
        </div>
    </div>
    </div>
    </div>
    </div>
    </div>
    <script>
        SyntaxHighlighter.all();
    </script>
</body>
</html>
""".strip()

#--- DOWNLOAD & UPDATE -------------------------------------------------------------------------------

for p in ("-", "-web", "-db", "-search", "-vector", "-graph", "-canvas", "-metrics", 
          "-de", "-en", "-es", "-fr", "-it", "-nl", 
          "-shell", "stop-words", "mbsp-tags", "-dev"):
    # We include some useful pages (Penn Treebank tags, stop words) referenced in the documentation.
    if p.startswith("-"):
        p = "pattern" + p.rstrip("-")
        title = p.replace("-", ".")
    if p == "stop-words":
        title = "Stop words"
    if p == "mbsp-tags":
        title = "Penn Treebank II tag set"
    # Download the online documentation pages.
    print("Retrieving", url + p)
    html = URL(url + p).download(cached=False)
    # Parse the actual documentation, we don't need the website header, footer, navigation, search.
    html = Document(html)
    html = html.by_id("content-area")
    html = html.by_class("node-type-page")[0]
    html = html.source
    html = strip_javascript(html)
    html = strip_between('<div id="navbar">', '/#navbar -->', html)
    html = strip_between('<div id="sidebar-right">', '/#sidebar-right -->', html)
    html = strip_between('<div id="footer">', '/#footer -->', html)
    html = strip_between('<a class="twitter-share-button"', '</a>', html)
    # Link to local pages and images.
    # Link to online media.
    html = html.replace('href="/pages/MBSP"', 'href="%sMBSP"' % url)                   # MBSP docs (online)
    html = re.sub('href="/pages/(pattern-examples.*?)"', 'href="%s\\1"' % url, html)   # examples (online)
    html = re.sub('href="/pages/(using-.*?)"', 'href="%s\\1"' % url, html)             # examples (online)
    html = re.sub('href="/pages/(modeling-.*?)"', 'href="%s\\1"' % url, html)          # examples (online)
    html = re.sub('href="/pages/(.*?)([#|"])', 'href="\\1.html\\2', html)              # pages (offline)
    html = html.replace('src="/media/', 'src="../g/')                                  # images (offline)
    html = html.replace('src="/sites/all/themes/clips/g/', 'src="../g/')               # images (offline)
    html = html.replace('href="/media/', 'href="%smedia/' % url.replace("pages/", "")) # downloads (online)
    # Apply the simplified template + set page titles.
    html = template % (p, url+p, url+p, title, html)
    # Generate offline HTML file.
    f = os.path.join(os.path.dirname(__file__), "html", "%s.html" % p)
    f = codecs.open(f, "w", encoding="utf-8")
    f.write(html)
    f.close()

# Create index.html (which simply redirects to pattern.html).
f = open(os.path.join(os.path.dirname(__file__), "index.html"), "w")
f.write('<meta http-equiv="refresh" content="0; url=html/pattern.html" />')
f.close()