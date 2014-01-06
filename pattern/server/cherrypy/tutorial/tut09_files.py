"""

Tutorial: File upload and download

Uploads
-------

When a client uploads a file to a CherryPy application, it's placed
on disk immediately. CherryPy will pass it to your exposed method
as an argument (see "myFile" below); that arg will have a "file"
attribute, which is a handle to the temporary uploaded file.
If you wish to permanently save the file, you need to read()
from myFile.file and write() somewhere else.

Note the use of 'enctype="multipart/form-data"' and 'input type="file"'
in the HTML which the client uses to upload the file.


Downloads
---------

If you wish to send a file to the client, you have two options:
First, you can simply return a file-like object from your page handler.
CherryPy will read the file and serve it as the content (HTTP body)
of the response. However, that doesn't tell the client that
the response is a file to be saved, rather than displayed.
Use cherrypy.lib.static.serve_file for that; it takes four
arguments:

serve_file(path, content_type=None, disposition=None, name=None)

Set "name" to the filename that you expect clients to use when they save
your file. Note that the "name" argument is ignored if you don't also
provide a "disposition" (usually "attachement"). You can manually set
"content_type", but be aware that if you also use the encoding tool, it
may choke if the file extension is not recognized as belonging to a known
Content-Type. Setting the content_type to "application/x-download" works
in most cases, and should prompt the user with an Open/Save dialog in
popular browsers.

"""

import os
localDir = os.path.dirname(__file__)
absDir = os.path.join(os.getcwd(), localDir)

import cherrypy
from cherrypy.lib import static


class FileDemo(object):

    def index(self):
        return """
        <html><body>
            <h2>Upload a file</h2>
            <form action="upload" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
            <h2>Download a file</h2>
            <a href='download'>This one</a>
        </body></html>
        """
    index.exposed = True

    def upload(self, myFile):
        out = """<html>
        <body>
            myFile length: %s<br />
            myFile filename: %s<br />
            myFile mime-type: %s
        </body>
        </html>"""

        # Although this just counts the file length, it demonstrates
        # how to read large files in chunks instead of all at once.
        # CherryPy reads the uploaded file into a temporary file;
        # myFile.file.read reads from that.
        size = 0
        while True:
            data = myFile.file.read(8192)
            if not data:
                break
            size += len(data)

        return out % (size, myFile.filename, myFile.content_type)
    upload.exposed = True

    def download(self):
        path = os.path.join(absDir, "pdf_file.pdf")
        return static.serve_file(path, "application/x-download",
                                 "attachment", os.path.basename(path))
    download.exposed = True


import os.path
tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(FileDemo(), config=tutconf)
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(FileDemo(), config=tutconf)
