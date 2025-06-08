from typing import ClassVar

from .compat import Template
from .node import HTMLElement, HTMLVoidElement



class TagMeta(type):
    element_class: ClassVar[type[HTMLElement]]

    def __new__(
        mcls, name: str, bases: tuple[type, ...], attrs: dict[str, object]
    ) -> type:
        if "tag" not in attrs:
            raise ValueError(f"{name} must define a 'tag' class attribute")
        if not isinstance(attrs["tag"], str):
            raise TypeError(f"{name}.tag must be a string")

        return super().__new__(mcls, name, bases, attrs)

    def __rshift__(
        self,
        other: type[HTMLElement]
        | HTMLElement
        | list[HTMLElement]
        | tuple[HTMLElement, ...]
        | None
        | str
        | Template,
    ) -> HTMLElement:
        return self() >> other

    def __matmul__(self, other: dict[str, str | Template]) -> HTMLElement:
        return self(**other)


# Root
html = TagMeta("HTMLRootElement", (HTMLElement,), {"tag": "html"})
head = TagMeta("HTMLHeadElement", (HTMLElement,), {"tag": "head"})
body = TagMeta("HTMLBodyElement", (HTMLElement,), {"tag": "body"})

# Metadata
base = TagMeta("HTMLBaseElement", (HTMLVoidElement,), {"tag": "base"})
link = TagMeta("HTMLLinkElement", (HTMLVoidElement,), {"tag": "link"})
meta = TagMeta("HTMLMetaElement", (HTMLVoidElement,), {"tag": "meta"})
style = TagMeta("HTMLStyleElement", (HTMLElement,), {"tag": "style"})
title = TagMeta("HTMLTitleElement", (HTMLElement,), {"tag": "title"})

# Sectioning
address = TagMeta("HTMLAddressElement", (HTMLElement,), {"tag": "address"})
article = TagMeta("HTMLArticleElement", (HTMLElement,), {"tag": "article"})
aside = TagMeta("HTMLAsideElement", (HTMLElement,), {"tag": "aside"})
footer = TagMeta("HTMLFooterElement", (HTMLElement,), {"tag": "footer"})
header = TagMeta("HTMLHeaderElement", (HTMLElement,), {"tag": "header"})
h1 = TagMeta("HTMLHeading1Element", (HTMLElement,), {"tag": "h1"})
h2 = TagMeta("HTMLHeading2Element", (HTMLElement,), {"tag": "h2"})
h3 = TagMeta("HTMLHeading3Element", (HTMLElement,), {"tag": "h3"})
h4 = TagMeta("HTMLHeading4Element", (HTMLElement,), {"tag": "h4"})
h5 = TagMeta("HTMLHeading5Element", (HTMLElement,), {"tag": "h5"})
h6 = TagMeta("HTMLHeading6Element", (HTMLElement,), {"tag": "h6"})
main = TagMeta("HTMLMainElement", (HTMLElement,), {"tag": "main"})
nav = TagMeta("HTMLNavElement", (HTMLElement,), {"tag": "nav"})
section = TagMeta("HTMLSectionElement", (HTMLElement,), {"tag": "section"})

# Grouping content
blockquote = TagMeta("HTMLBlockquoteElement", (HTMLElement,), {"tag": "blockquote"})
dd = TagMeta("HTMLDDElement", (HTMLElement,), {"tag": "dd"})
div = TagMeta("HTMLDivElement", (HTMLElement,), {"tag": "div"})
dl = TagMeta("HTMLDLElement", (HTMLElement,), {"tag": "dl"})
dt = TagMeta("HTMLDTElement", (HTMLElement,), {"tag": "dt"})
figcaption = TagMeta("HTMLFigcaptionElement", (HTMLElement,), {"tag": "figcaption"})
figure = TagMeta("HTMLFigureElement", (HTMLElement,), {"tag": "figure"})
hr = TagMeta("HTMLHRElement", (HTMLVoidElement,), {"tag": "hr"})
li = TagMeta("HTMLLIElement", (HTMLElement,), {"tag": "li"})
ol = TagMeta("HTMLOLElement", (HTMLElement,), {"tag": "ol"})
p = TagMeta("HTMLParagraphElement", (HTMLElement,), {"tag": "p"})
pre = TagMeta("HTMLPreElement", (HTMLElement,), {"tag": "pre"})
ul = TagMeta("HTMLULElement", (HTMLElement,), {"tag": "ul"})
# Text-level semantics
a = TagMeta("HTMLAnchorElement", (HTMLElement,), {"tag": "a"})
abbr = TagMeta("HTMLAbbrElement", (HTMLElement,), {"tag": "abbr"})
b = TagMeta("HTMLBoldElement", (HTMLElement,), {"tag": "b"})
bdi = TagMeta("HTMLBdiElement", (HTMLElement,), {"tag": "bdi"})
bdo = TagMeta("HTMLBdoElement", (HTMLElement,), {"tag": "bdo"})
br = TagMeta("HTMLBRElement", (HTMLVoidElement,), {"tag": "br"})
cite = TagMeta("HTMLCiteElement", (HTMLElement,), {"tag": "cite"})
code = TagMeta("HTMLCodeElement", (HTMLElement,), {"tag": "code"})
data = TagMeta("HTMLDataElement", (HTMLElement,), {"tag": "data"})
dfn = TagMeta("HTMLDfnElement", (HTMLElement,), {"tag": "dfn"})
em = TagMeta("HTMLEmElement", (HTMLElement,), {"tag": "em"})
i = TagMeta("HTMLItalicElement", (HTMLElement,), {"tag": "i"})
kbd = TagMeta("HTMLKbdElement", (HTMLElement,), {"tag": "kbd"})
mark = TagMeta("HTMLMarkElement", (HTMLElement,), {"tag": "mark"})
q = TagMeta("HTMLQuoteElement", (HTMLElement,), {"tag": "q"})
rp = TagMeta("HTMLRpElement", (HTMLElement,), {"tag": "rp"})
rt = TagMeta("HTMLRtElement", (HTMLElement,), {"tag": "rt"})
ruby = TagMeta("HTMLRubyElement", (HTMLElement,), {"tag": "ruby"})
s = TagMeta("HTMLSElement", (HTMLElement,), {"tag": "s"})
samp = TagMeta("HTMLSampElement", (HTMLElement,), {"tag": "samp"})
small = TagMeta("HTMLSmallElement", (HTMLElement,), {"tag": "small"})
span = TagMeta("HTMLSpanElement", (HTMLElement,), {"tag": "span"})
strong = TagMeta("HTMLStrongElement", (HTMLElement,), {"tag": "strong"})
sub = TagMeta("HTMLSubElement", (HTMLElement,), {"tag": "sub"})
sup = TagMeta("HTMLSupElement", (HTMLElement,), {"tag": "sup"})
time = TagMeta("HTMLTimeElement", (HTMLElement,), {"tag": "time"})
u = TagMeta("HTMLUElement", (HTMLElement,), {"tag": "u"})
var = TagMeta("HTMLVarElement", (HTMLElement,), {"tag": "var"})
wbr = TagMeta("HTMLWBRElement", (HTMLVoidElement,), {"tag": "wbr"})

# Edits
del_ = TagMeta("HTMLDelElement", (HTMLElement,), {"tag": "del"})
ins = TagMeta("HTMLInsElement", (HTMLElement,), {"tag": "ins"})

# Embedded content
area = TagMeta("HTMLAreaElement", (HTMLVoidElement,), {"tag": "area"})
audio = TagMeta("HTMLAudioElement", (HTMLElement,), {"tag": "audio"})
img = TagMeta("HTMLImageElement", (HTMLVoidElement,), {"tag": "img"})
map_ = TagMeta("HTMLMapElement", (HTMLElement,), {"tag": "map"})
track = TagMeta("HTMLTrackElement", (HTMLVoidElement,), {"tag": "track"})
video = TagMeta("HTMLVideoElement", (HTMLElement,), {"tag": "video"})
embed = TagMeta("HTMLEmbedElement", (HTMLVoidElement,), {"tag": "embed"})
iframe = TagMeta("HTMLIFrameElement", (HTMLElement,), {"tag": "iframe"})
object_ = TagMeta("HTMLObjectElement", (HTMLElement,), {"tag": "object"})
picture = TagMeta("HTMLPictureElement", (HTMLElement,), {"tag": "picture"})
portal = TagMeta("HTMLPortalElement", (HTMLElement,), {"tag": "portal"})
source = TagMeta("HTMLSourceElement", (HTMLVoidElement,), {"tag": "source"})

# Scripting
canvas = TagMeta("HTMLCanvasElement", (HTMLElement,), {"tag": "canvas"})
noscript = TagMeta("HTMLNoscriptElement", (HTMLElement,), {"tag": "noscript"})
script = TagMeta("HTMLScriptElement", (HTMLElement,), {"tag": "script"})

# Demarcating edits
del_ = TagMeta("HTMLDelElement", (HTMLElement,), {"tag": "del"})
ins = TagMeta("HTMLInsElement", (HTMLElement,), {"tag": "ins"})

# Table content
caption = TagMeta("HTMLCaptionElement", (HTMLElement,), {"tag": "caption"})
col = TagMeta("HTMLColElement", (HTMLVoidElement,), {"tag": "col"})
colgroup = TagMeta("HTMLColgroupElement", (HTMLElement,), {"tag": "colgroup"})
table = TagMeta("HTMLTableElement", (HTMLElement,), {"tag": "table"})
tbody = TagMeta("HTMLTbodyElement", (HTMLElement,), {"tag": "tbody"})
td = TagMeta("HTMLTdElement", (HTMLElement,), {"tag": "td"})
tfoot = TagMeta("HTMLTfootElement", (HTMLElement,), {"tag": "tfoot"})
th = TagMeta("HTMLThElement", (HTMLElement,), {"tag": "th"})
thead = TagMeta("HTMLTheadElement", (HTMLElement,), {"tag": "thead"})
tr = TagMeta("HTMLTrElement", (HTMLElement,), {"tag": "tr"})

# Forms
button = TagMeta("HTMLButtonElement", (HTMLElement,), {"tag": "button"})
datalist = TagMeta("HTMLDatalistElement", (HTMLElement,), {"tag": "datalist"})
fieldset = TagMeta("HTMLFieldsetElement", (HTMLElement,), {"tag": "fieldset"})
form = TagMeta("HTMLFormElement", (HTMLElement,), {"tag": "form"})
input_ = TagMeta("HTMLInputElement", (HTMLVoidElement,), {"tag": "input"})
label = TagMeta("HTMLLabelElement", (HTMLElement,), {"tag": "label"})
legend = TagMeta("HTMLLegendElement", (HTMLElement,), {"tag": "legend"})
meter = TagMeta("HTMLMeterElement", (HTMLElement,), {"tag": "meter"})
optgroup = TagMeta("HTMLOptgroupElement", (HTMLElement,), {"tag": "optgroup"})
option = TagMeta("HTMLOptionElement", (HTMLElement,), {"tag": "option"})
output = TagMeta("HTMLOutputElement", (HTMLElement,), {"tag": "output"})
progress = TagMeta("HTMLProgressElement", (HTMLElement,), {"tag": "progress"})
select = TagMeta("HTMLSelectElement", (HTMLElement,), {"tag": "select"})
textarea = TagMeta("HTMLTextAreaElement", (HTMLElement,), {"tag": "textarea"})

# Interactive elements
details = TagMeta("HTMLDetailsElement", (HTMLElement,), {"tag": "details"})
dialog = TagMeta("HTMLDialogElement", (HTMLElement,), {"tag": "dialog"})
menu = TagMeta("HTMLMenuElement", (HTMLElement,), {"tag": "menu"})
summary = TagMeta("HTMLSummaryElement", (HTMLElement,), {"tag": "summary"})

# Web Components
slot = TagMeta("HTMLSlotElement", (HTMLElement,), {"tag": "slot"})
template = TagMeta("HTMLTemplateElement", (HTMLElement,), {"tag": "template"})
