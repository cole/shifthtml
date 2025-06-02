import sys

if sys.version_info >= (3, 14):
    from string.templatelib import Interpolation, Template
else:
    class Template(str):
        pass
    class Interpolation:
        pass
