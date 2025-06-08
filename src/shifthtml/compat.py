import sys

if sys.version_info >= (3, 14):
    from string.templatelib import Interpolation, Template
else:
    # Dummy classes for import compatibility
    class Template(str):
        pass
    class Interpolation:
        def __match_args__(self):
            return ("value", "name", "conversion", "format_spec")
