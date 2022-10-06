import os
import ast
import fnmatch
from pathlib import Path
from click import echo

from inferex.utils.io.logs import get_logger


logger = get_logger(__name__)

# TODO: dynamically generate this modules list
BUILTIN_MODULES = """__future__
__main__
_dummy_thread
_thread
abc
aifc
and
argparse
array
ast
asynchat
asyncio
asyncore
atexit
audioop
base64
bdb
binascii
binhex
bisect
builtins
bytes
bz2
calendar
cgi
cgitb
chunk
cmath
cmd
code
codecs
codeop
collections
colorsys
compileall
concurrent
configparser
contextlib
contextvars
copy
copyreg
crypt
csv
ctypes
curses
dataclasses
datetime
dbm
decimal
dict
difflib
dis
distutils
doctest
dummy_threading
email
ensurepip
enum
errno
faulthandler
fcntl
filecmp
fileinput
fnmatch
formatter
fractions
ftplib
functools
gc
getopt
getpass
gettext
glob
grp
gzip
hashlib
heapq
hmac
html
http
imaplib
imghdr
imp
importlib
inspect
int
io
ipaddress
itertools
json
keyword
linecache
list
locale
logging
lzma
mailbox
mailcap
marshal
math
mimetypes
mmap
modulefinder
msilib
msvcrt
multiprocessing
netrc
nis
nntplib
numbers
operator
optparse
os
ossaudiodev
parser
pathlib
pdb
pickle
pickletools
pipes
pkgutil
platform
plistlib
poplib
posix
pprint
pty
pwd
py_compile
pyclbr
pydoc
queue
quopri
random
re
readline
reprlib
resource
rlcompleter
runpy
sched
secrets
select
selectors
set
shelve
shlex
shutil
signal
site
smtpd
smtplib
sndhdr
socket
socketserver
spwd
sqlite3
ssl
stat
statistics
str
string
stringprep
struct
subprocess
sunau
symbol
symtable
sys
sysconfig
syslog
tabnanny
tarfile
telnetlib
tempfile
termios
test
textwrap
threading
time
timeit
tkinter
token
tokenize
trace
traceback
tracemalloc
tty
turtle
types
typing
unicodedata
unittest
urllib
uu
uuid
venv
warnings
wave
weakref
webbrowser
winreg
winsound
wsgiref
xdrlib
xml
xmlrpc
zipapp
zipfile
zipimport
zlib""".split("\n")

class RequirementsValidationException(Exception):
    pass

def scan_requirements(project_dir: Path) -> list:
    """
    Read requirements.txt and return a list of dependencies.

    Args:
        project_dir(Path): Path to the project directory.

    Returns:
        names(list): a list of requirements found in requirements.txt
    """
    requirements_path = project_dir / "requirements.txt"
    try:
        with open(requirements_path, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        logger.warning(f"No requirements.txt found in {project_dir}")
        lines = []

    names = []
    for l in lines:
        if l.startswith('#'):
            continue
        l = l.replace("<", " ").replace(">", " ").replace("=", " ")
        l = l.replace("~", " ").replace("!", " ").replace("-", "_")
        if l := l.split(" ")[0].strip():
            names.append(l)

    return names


def pre_walk_dir_check(path: str) -> None:
    """
    Check the to-be-deployed directory for .py files up to two levels deep.
    If there are none, raise an exception.

    Example: a user issues `inferex deploy` from their root directory. Instead
    of recursively walking all folders and files, exit early.

    Args:
        path(str): the project directory to check

    Raises:
        Exception: if there are no python files in the project dir, or in
                   subfolders 1 level beneath the project dir.
    """
    project_root_files = list(fnmatch.filter(os.listdir(path), "*.py"))
    project_root_folders = [p for p in os.listdir(path) if os.path.isdir(p)]
    subfolder_python_files = []
    for folder in project_root_folders:
        subfolder_python_files.extend(list(fnmatch.filter(os.listdir(folder), "*.py")))

    if not project_root_files and not subfolder_python_files:
        raise Exception(
            f"No python files found in or directly beneath {path}. "
            "Is this the right directory?"
        )



def is_standard_lib(module: str) -> bool:
    """
    Check if a module is in a predefined list of standard library module names.

    Args:
        module(str): the module name to check.

    Returns:
        bool: True if the module is contained within BUILTIN_MODULES.
              False otherwise.
    """
    return module in BUILTIN_MODULES


def get_python_filepaths(path: str) -> list:
    """ Given a directory, look for '*.py" files recursively and return a list
        of filepaths.

    Args:
        path(str): the project directory to check

    Returns:
        python_filepaths(list): a list of fullpaths to python files in the
            project directory.
    """
    pre_walk_dir_check(path)
    python_filepaths = []
    for root, _, filenames in os.walk(path):
        python_filepaths.extend(
            os.path.join(
                root, filename
            ) for filename in fnmatch.filter(filenames, "*.py")
        )

    return python_filepaths


def get_imports(path: str) -> list:
    """
    Returns a list of imports in a project.

    Args:
        path(str): the project directory to check

    Returns:
        modules(list): a list of distinct modules imported throughout the
            project folder.
    """
    python_filepaths = get_python_filepaths(path)
    modules = []
    for python_file in python_filepaths:
        with open(python_file) as file:
            root = ast.parse(file.read(), path)

        for node in ast.walk(root):
            if isinstance(node, ast.Import):
                for name in node.names:
                    module = name.name.split('.')[0]
                    modules.append(module)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module.split('.')[0])
            else:
                continue

    return list(set(modules))


def validate_requirements_txt(path: str) -> None:
    """
    Validate a project's imports against its requirements.txt.

    Args:
        path(str): the project directory to check

    Raises:
        ValueError: if there's a dependency not listed in requirements.txt
    """
    requirements = scan_requirements(path)
    imported_modules = get_imports(path)
    for module in imported_modules:
        if is_standard_lib(module) or module == "inferex":
            continue

        if module not in requirements:
            # TODO: solve edge cases
            # raise RequirementsValidationException(f"Expected imported module '{module}' to be in requirements.txt")
            echo(f"!!! Expected imported module '{module}' to be in requirements.txt")

    # warn about unused dependencies found in requirements.txt
    if unused_dependencies := [r for r in requirements if r not in imported_modules]:
        logger.warning(
            f"Unused dependencies found: {', '.join(unused_dependencies)}. "
            "Removing these could improve deployment time."
        )
