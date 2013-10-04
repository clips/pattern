###########
Python docx
###########

Introduction
============

The docx module creates, reads and writes Microsoft Office Word 2007 docx
files.

These are referred to as 'WordML', 'Office Open XML' and 'Open XML' by
Microsoft.

These documents can be opened in Microsoft Office 2007 / 2010, Microsoft Mac
Office 2008, Google Docs, OpenOffice.org 3, and Apple iWork 08.

They also `validate as well formed XML <http://validator.w3.org/check>`_.

The module was created when I was looking for a Python support for MS Word
.docx files, but could only find various hacks involving COM automation,
calling .Net or Java, or automating OpenOffice or MS Office.

The docx module has the following features:

Making documents
----------------

Features for making documents include:

- Paragraphs
- Bullets
- Numbered lists
- Document properties (author, company, etc)
- Multiple levels of headings
- Tables
- Section and page breaks
- Images

.. image:: http://github.com/mikemaccana/python-docx/raw/master/screenshot.png


Editing documents
-----------------

Thanks to the awesomeness of the lxml module, we can:

- Search and replace
- Extract plain text of document
- Add and delete items anywhere within the document
- Change document properties
- Run xpath queries against particular locations in the document - useful for
  retrieving data from user-completed templates.


Getting started
===============

Making and Modifying Documents
------------------------------

- Just `download python docx <http://github.com/mikemaccana/python-docx/tarball/master>`_.
- Use **pip** or **easy_install** to fetch the **lxml** and **PIL** modules.
- Then run::

    example-makedocument.py


Congratulations, you just made and then modified a Word document!


Extracting Text from a Document
-------------------------------

If you just want to extract the text from a Word file, run::

    example-extracttext.py 'Some word file.docx' 'new file.txt'


Ideas & To Do List
~~~~~~~~~~~~~~~~~~

- Further improvements to image handling
- Document health checks
- Egg
- Markdown conversion support


We love forks, changes and pull requests!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Check out the [HACKING](HACKING.markdown) to add your own changes!
- For this project on github
- Send a pull request via github and we'll add your changes!

Want to talk? Need help?
~~~~~~~~~~~~~~~~~~~~~~~~

Email python-docx@googlegroups.com


License
~~~~~~~

Licensed under the `MIT license <http://www.opensource.org/licenses/mit-license.php>`_

Short version: this code is copyrighted to me (Mike MacCana), I give you
permission to do what you want with it except remove my name from the credits.
See the LICENSE file for specific terms.
