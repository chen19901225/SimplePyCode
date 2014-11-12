from locale import normalize
import string
from stringold import upper
from PIL.ImageOps import flip


def addfactory(n):
    return lambda m,n=n:m+n

from operator import mul, add, truth
apply_each = lambda fns, args=[]: map(apply, fns, [args]*len(fns))
bools = lambda st: map(truth, st)
bool_each = lambda fns, args=[]: bools(apply_each(fns, args))
conjoin = lambda fns, args=[]: reduce(mul, bool_each(fns, args))
all = lambda fns: lambda arg, fns=fns: conjoin(fns, (arg,))
both = lambda f,g: all((f,g))
all3 = lambda f,g,h: all((f,g,h))
and_ = lambda f,g: lambda x, f=f, g=g: f(x) and g(x)
disjoin = lambda fns, args=[]: reduce(add, bool_each(fns, args))
some = lambda fns: lambda arg, fns=fns: disjoin(fns, (arg,))
either = lambda f,g: some((f,g))
anyof3 = lambda f,g,h: some((f,g,h))
compose = lambda f,g: lambda x, f=f, g=g: f(g(x))
compose3 = lambda f,g,h: lambda x, f=f, g=g, h=h: f(g(h(x)))
ident = lambda x: x


if __name__=="__main__":
    capFlipNorm=compose3(upper, string.expandtabs,normalize)
    text_str="""
    Title: Python 2.2
Source: C:\DOWNLOAD\PYTHON-2.2.EXE | 02-23-2002 | 01:40:54 | 7074248
Made Dir: D:\Python22
File Copy: D:\Python22\UNWISE.EXE | 05-24-2001 | 12:59:30 | | ...
RegDB Key: Software\Microsoft\Windows\CurrentVersion\Uninstall\Py...
RegDB Val: Python 2.2
File Copy: D:\Python22\w9xpopen.exe | 12-21-2001 | 12:22:34 | | ...
Made Dir: D:\PYTHON22\DLLs
File Overwrite: C:\WINDOWS\SYSTEM\MSVCRT.DLL | | | | 295000 | 770c8856
RegDB Root: 2
RegDB Key: Software\Microsoft\Windows\CurrentVersion\App Paths\Py...
RegDB Val: D:\PYTHON22\Python.exe
Shell Link: C:\WINDOWS\Start Menu\Programs\Python 2.2\Uninstall Py...
Link Info: D:\Python22\UNWISE.EXE | D:\PYTHON22 | | 0 | 1 | 0 |
Shell Link: C:\WINDOWS\Start Menu\Programs\Python 2.2\Python ...
Link Info: D:\Python22\python.exe | D:\PYTHON22 | D:\PYTHON22\...
    """
    lines=text_str.splitlines()
    cap_flip_norms=map(capFlipNorm,lines)

    print apply_each(map(addfactory,range(5)),(10,))