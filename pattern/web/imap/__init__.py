#### PATTERN | WEB | IMAP ##########################################################################
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

####################################################################################################

import sys
import os
import re
import imaplib
import email
import time

try: 
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

# Import the Cache class from pattern.web so e-mails can be cached locally (faster):
try: from ..cache import cache
except:
    try: 
        import os, sys; sys.path.append(os.path.join(MODULE, ".."))
        from cache import cache
    except:
        try:
            from pattern.web.cache import cache
        except:
            cache = {}

#### STRING FUNCTIONS ##############################################################################

def decode_utf8(string):
    """ Returns the given string as a unicode string (if possible).
    """
    if isinstance(string, str):
        for encoding in (("utf-8",), ("windows-1252",), ("utf-8", "ignore")):
            try: 
                return string.decode(*encoding)
            except:
                pass
        return string
    return unicode(string)
    
def encode_utf8(string):
    """ Returns the given string as a Python byte string (if possible).
    """
    if isinstance(string, unicode):
        try: 
            return string.encode("utf-8")
        except:
            return string
    return str(string)

#### IMAP4 SSL #####################################################################################
# Fixes an issue in Python 2.5- with memory allocation.
# See: http://bugs.python.org/issue1389051

if sys.version_info[:2] > (2, 5):
    
    class IMAP4(imaplib.IMAP4):
        pass
        
    class IMAP4_SSL(imaplib.IMAP4_SSL):
        pass
        
else:

    class IMAP4(imaplib.IMAP4):
        pass

    class IMAP4_SSL(imaplib.IMAP4_SSL):
        def read(self, size):
            """Read 'size' bytes from remote."""
            # sslobj.read() sometimes returns < size bytes
            chunks = []
            read = 0
            while read < size:
                data = self.sslobj.read(min(size-read, 16384))
                read += len(data)
                chunks.append(data)
            return ''.join(chunks)

#### MAIL ##########################################################################################

GMAIL = "imap.gmail.com"

DATE, FROM, SUBJECT, BODY, ATTACHMENTS = \
    "date", "from", "subject", "body", "attachments"
    
def _basename(folder):
    # [Gmail]/INBOX => inbox
    f = folder.replace("[Gmail]/","")
    f = f.replace("[Gmail]","")
    f = f.replace("Mail", "")   # "Sent Mail" alias = "sent".
    f = f.replace("INBOX.", "") # "inbox.sent" alias = "sent".
    f = f.lower()
    f = f.strip()
    return f

class MailError(Exception):
    pass
class MailServiceError(MailError):
    pass
class MailLoginError(MailError):
    pass
class MailNotLoggedIn(MailError):
    pass

class Mail(object):
    
    def __init__(self, username, password, service=GMAIL, port=993, secure=True):
        """ IMAP4 connection to a mailbox. With secure=True, SSL is used. 
            The standard port for SSL is 993.
            The standard port without SSL is 143.
        """
        self._username = username
        self._password = password
        self._host     = service
        self._port     = port
        self._secure   = secure
        self._imap4    = None
        self._folders  = None
        self.login(username, password)

    @property
    def _id(self):
        return "%s:%s@%s:%s" % (self._username, self._password, self._host, self._port)

    @property
    def imap4(self):
        if self._imap4 is None: 
            raise MailNotLoggedIn
        return self._imap4
 
    def login(self, username, password, **kwargs):
        """ Signs in to the mail account with the given username and password,
            raises a MailLoginError otherwise.
        """
        self.logout()
        self._secure = kwargs.get("secure", self._secure)
        self._imap4 = (self._secure and IMAP4_SSL or IMAP4)(self._host, self._port)
        try:
            status, response = self._imap4.login(username, password)
        except:
            raise MailLoginError
        if status != "OK":
            raise MailLoginError(response)
 
    def logout(self):
        """ Signs out of the mail account.
        """
        if self._imap4 is not None:
            self._imap4.logout()
            self._imap4 = None
        
    def __del__(self):
        if "_imap4" in self.__dict__:
            if self._imap4 is not None:
                self._imap4.logout()
                self._imap4 = None
    
    @property
    def folders(self):
        """ A dictionary of (name, MailFolder)-tuples.
            Default folders: inbox, trash, spam, receipts, ...
        """
        if self._folders is None:
            status, response = self.imap4.list()
            self._folders = [f.split(" \"")[-1].strip(" \"") for f in response]
            self._folders = [(_basename(f), MailFolder(self, f)) for f in self._folders]
            self._folders = [(f, o) for f, o in self._folders if f != ""]
            self._folders = dict(self._folders)
        return self._folders
    
    def __getattr__(self, k):
        """ Each folder is accessible as Mail.[name].
        """
        if k in self.__dict__:
            return self.__dict__[k]
        if k in self.folders:
            return self.folders[k]
        raise AttributeError("'Mail' object has no attribute '%s'" % k)

#--- MAIL FOLDER -----------------------------------------------------------------------------------

def _decode(s, message):
    try:
        # Decode MIME header (e.g., "=?utf-8?q?").
        s = email.Header.decode_header(s)[0][0]
    except:
        pass
    try:
        # Decode message Content-Type charset to Unicode.
        # If all fails, try Latin-1 (common case).
        e = message.get("Content-Type")
        e = e.split("charset=")[-1].split(";")[0].strip("\"'").lower()
        s = s.decode(e)
    except:
        try: s = s.decode("utf-8")
        except:
            try: s = s.decode("latin-1")
            except: 
                pass 
    return s

class MailFolder(object):
    
    def __init__(self, parent, name):
        """ A folder (inbox, spam, trash, ...) in a mailbox.
            E-mail messages can be searched and retrieved (including attachments) from a folder.
        """
        self._parent = parent
        self._name   = name
    
    @property
    def parent(self):
        return self._parent
    
    @property
    def name(self):
        return _basename(self._name)
    
    @property
    def count(self):
        return len(self)

    def search(self, q, field=FROM, cached=False):
        """ Returns a list of indices for the given query, latest-first.
            The search field can be FROM, DATE or SUBJECT.
        """
        id = "mail-%s-%s-%s-%s" % (self.parent._id, self.name, q, field)
        if cached and id in cache:
            status, response = "OK", [cache[id]]
        else:
            status, response = self.parent.imap4.select(self._name, readonly=1)
            status, response = self.parent.imap4.search(None, field.upper(), q)
            if cached:
                cache[id] = response[0]
        return sorted([int(i)-1 for i in response[0].split()], reverse=True)

    def read(self, i, attachments=False, cached=True):
        return self.__getitem__(i, attachments, cached)
    
    def __getitem__(self, i, attachments=False, cached=True):
        """ Returns the mail message with the given index.
            Each message is a dictionary with date, from, subject, body, attachments entries.
            The attachments entry is a list of (MIME-type, str)-tuples.
        """
        i += 1
        id = "mail-%s-%s-%s-%s" % (self.parent._id, self.name, i, attachments)
        if cached and id in cache:
            m = cache[id]
        else:
            # Select the current mail folder.
            # Get the e-mail header.
            # Get the e-mail body, with or without file attachments.
            status, response  = self.parent.imap4.select(self._name, readonly=1)
            status, response1 = self.parent.imap4.fetch(str(i), '(BODY.PEEK[HEADER])')
            status, response2 = self.parent.imap4.fetch(str(i), '(BODY.PEEK[%s])' % (not attachments and "TEXT" or ""))
            time.sleep(0.1)
            m = response1[0][1] + response2[0][1]
            # Cache the raw message for faster retrieval.
            if cached:
                cache[id] = m
        # Parse the raw message.
        m = email.message_from_string(encode_utf8(m))
        d = Message([
                 (DATE, _decode(m.get(DATE), m)),
                 (FROM, _decode(m.get(FROM), m)),
              (SUBJECT, _decode(m.get(SUBJECT), m)),
                 (BODY, ""),
          (ATTACHMENTS, [])])
        # Message body can be a list of parts, including file attachments.
        for p in (m.is_multipart() and m.get_payload() or [m]):
            if p.get_content_type() == "text/plain":
                d[BODY] += _decode(p.get_payload(decode=True), p)
            elif attachments:
                d[ATTACHMENTS].append((p.get_content_type(), p.get_payload()))
        for k in d:
            if isinstance(d[k], basestring):
                d[k] = d[k].strip()
                d[k] = d[k].replace("\r\n", "\n")
        return d
        
    def __iter__(self):
        """ Returns an iterator over all the messages in the folder, latest-first.
        """
        for i in reversed(range(len(self))):
            yield self[i]

    def __len__(self):
        status, response = self.parent.imap4.select(self.name, readonly=1)
        return int(response[0])

    def __repr__(self):
        return "MailFolder(name=%s)" % repr(self.name)

#--- MAIL MESSAGE ----------------------------------------------------------------------------------

class Message(dict):
    
    @property
    def author(self):
        return self.get(FROM, None)
    @property
    def date(self):
        return self.get(DATE, None)
    @property
    def subject(self):
        return self.get(SUBJECT, "")
    @property
    def body(self):
        return self.get(BODY, "")
    @property
    def attachments(self):
        return self.get(ATTACHMENTS, [])

    @property
    def email_address(self):
        m = re.search(r"<(.*?)>", self.author)
        return m and m.group(1) or ""

    def __repr__(self):
        return "Message(from=%s, subject=%s)" % (
            repr(self.author),
            repr(self.subject))
