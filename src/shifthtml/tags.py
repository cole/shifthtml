from __future__ import annotations

from .element import Element, VoidElement
from .meta import TagMeta

# Root
html = TagMeta("HTMLRootElement", (Element,), {"tag": "html"})
head = TagMeta("HTMLHeadElement", (Element,), {"tag": "head"})
body = TagMeta("HTMLBodyElement", (Element,), {"tag": "body"})

# Metadata
base = TagMeta("HTMLBaseElement", (VoidElement,), {"tag": "base"})
link = TagMeta("HTMLLinkElement", (VoidElement,), {"tag": "link"})
meta = TagMeta("HTMLMetaElement", (VoidElement,), {"tag": "meta"})
style = TagMeta("HTMLStyleElement", (Element,), {"tag": "style"})
title = TagMeta("HTMLTitleElement", (Element,), {"tag": "title"})

# Sectioning
address = TagMeta("HTMLAddressElement", (Element,), {"tag": "address"})
article = TagMeta("HTMLArticleElement", (Element,), {"tag": "article"})
aside = TagMeta("HTMLAsideElement", (Element,), {"tag": "aside"})
footer = TagMeta("HTMLFooterElement", (Element,), {"tag": "footer"})
header = TagMeta("HTMLHeaderElement", (Element,), {"tag": "header"})
h1 = TagMeta("HTMLHeading1Element", (Element,), {"tag": "h1"})
h2 = TagMeta("HTMLHeading2Element", (Element,), {"tag": "h2"})
h3 = TagMeta("HTMLHeading3Element", (Element,), {"tag": "h3"})
h4 = TagMeta("HTMLHeading4Element", (Element,), {"tag": "h4"})
h5 = TagMeta("HTMLHeading5Element", (Element,), {"tag": "h5"})
h6 = TagMeta("HTMLHeading6Element", (Element,), {"tag": "h6"})
main = TagMeta("HTMLMainElement", (Element,), {"tag": "main"})
nav = TagMeta("HTMLNavElement", (Element,), {"tag": "nav"})
section = TagMeta("HTMLSectionElement", (Element,), {"tag": "section"})

# Grouping content
blockquote = TagMeta("HTMLBlockquoteElement", (Element,), {"tag": "blockquote"})
dd = TagMeta("HTMLDDElement", (Element,), {"tag": "dd"})
div = TagMeta("HTMLDivElement", (Element,), {"tag": "div"})
dl = TagMeta("HTMLDLElement", (Element,), {"tag": "dl"})
dt = TagMeta("HTMLDTElement", (Element,), {"tag": "dt"})
figcaption = TagMeta("HTMLFigcaptionElement", (Element,), {"tag": "figcaption"})
figure = TagMeta("HTMLFigureElement", (Element,), {"tag": "figure"})
hr = TagMeta("HTMLHrElement", (VoidElement,), {"tag": "hr"})
li = TagMeta("HTMLLiElement", (Element,), {"tag": "li"})
ol = TagMeta("HTMLOlElement", (Element,), {"tag": "ol"})
p = TagMeta("HTMLParagraphElement", (Element,), {"tag": "p"})
pre = TagMeta("HTMLPreElement", (Element,), {"tag": "pre"})
ul = TagMeta("HTMLUlElement", (Element,), {"tag": "ul"})
# Text-level semantics
a = TagMeta("HTMLAnchorElement", (Element,), {"tag": "a"})
abbr = TagMeta("HTMLAbbrElement", (Element,), {"tag": "abbr"})
b = TagMeta("HTMLBoldElement", (Element,), {"tag": "b"})
bdi = TagMeta("HTMLBdiElement", (Element,), {"tag": "bdi"})
bdo = TagMeta("HTMLBdoElement", (Element,), {"tag": "bdo"})
br = TagMeta("HTMLBRElement", (VoidElement,), {"tag": "br"})
cite = TagMeta("HTMLCiteElement", (Element,), {"tag": "cite"})
code = TagMeta("HTMLCodeElement", (Element,), {"tag": "code"})
data = TagMeta("HTMLDataElement", (Element,), {"tag": "data"})
dfn = TagMeta("HTMLDfnElement", (Element,), {"tag": "dfn"})
em = TagMeta("HTMLEmElement", (Element,), {"tag": "em"})
i = TagMeta("HTMLItalicElement", (Element,), {"tag": "i"})
kbd = TagMeta("HTMLKbdElement", (Element,), {"tag": "kbd"})
mark = TagMeta("HTMLMarkElement", (Element,), {"tag": "mark"})
q = TagMeta("HTMLQuoteElement", (Element,), {"tag": "q"})
rp = TagMeta("HTMLRpElement", (Element,), {"tag": "rp"})
rt = TagMeta("HTMLRtElement", (Element,), {"tag": "rt"})
ruby = TagMeta("HTMLRubyElement", (Element,), {"tag": "ruby"})
s = TagMeta("HTMLSElement", (Element,), {"tag": "s"})
samp = TagMeta("HTMLSampElement", (Element,), {"tag": "samp"})
small = TagMeta("HTMLSmallElement", (Element,), {"tag": "small"})
span = TagMeta("HTMLSpanElement", (Element,), {"tag": "span"})
strong = TagMeta("HTMLStrongElement", (Element,), {"tag": "strong"})
sub = TagMeta("HTMLSubElement", (Element,), {"tag": "sub"})
sup = TagMeta("HTMLSupElement", (Element,), {"tag": "sup"})
time = TagMeta("HTMLTimeElement", (Element,), {"tag": "time"})
u = TagMeta("HTMLUElement", (Element,), {"tag": "u"})
var = TagMeta("HTMLVarElement", (Element,), {"tag": "var"})
wbr = TagMeta("HTMLWBRElement", (VoidElement,), {"tag": "wbr"})

# Edits
del_ = TagMeta("HTMLDelElement", (Element,), {"tag": "del"})
ins = TagMeta("HTMLInsElement", (Element,), {"tag": "ins"})

# Embedded content
area = TagMeta("HTMLAreaElement", (VoidElement,), {"tag": "area"})
audio = TagMeta("HTMLAudioElement", (Element,), {"tag": "audio"})
img = TagMeta("HTMLImageElement", (VoidElement,), {"tag": "img"})
map_ = TagMeta("HTMLMapElement", (Element,), {"tag": "map"})
track = TagMeta("HTMLTrackElement", (VoidElement,), {"tag": "track"})
video = TagMeta("HTMLVideoElement", (Element,), {"tag": "video"})
embed = TagMeta("HTMLEmbedElement", (VoidElement,), {"tag": "embed"})
iframe = TagMeta("HTMLIFrameElement", (Element,), {"tag": "iframe"})
object_ = TagMeta("HTMLObjectElement", (Element,), {"tag": "object"})
picture = TagMeta("HTMLPictureElement", (Element,), {"tag": "picture"})
portal = TagMeta("HTMLPortalElement", (Element,), {"tag": "portal"})
source = TagMeta("HTMLSourceElement", (VoidElement,), {"tag": "source"})

# Scripting
canvas = TagMeta("HTMLCanvasElement", (Element,), {"tag": "canvas"})
noscript = TagMeta("HTMLNoscriptElement", (Element,), {"tag": "noscript"})
script = TagMeta("HTMLScriptElement", (Element,), {"tag": "script"})

# Table content
caption = TagMeta("HTMLCaptionElement", (Element,), {"tag": "caption"})
col = TagMeta("HTMLColElement", (VoidElement,), {"tag": "col"})
colgroup = TagMeta("HTMLColgroupElement", (Element,), {"tag": "colgroup"})
table = TagMeta("HTMLTableElement", (Element,), {"tag": "table"})
tbody = TagMeta("HTMLTbodyElement", (Element,), {"tag": "tbody"})
td = TagMeta("HTMLTdElement", (Element,), {"tag": "td"})
tfoot = TagMeta("HTMLTfootElement", (Element,), {"tag": "tfoot"})
th = TagMeta("HTMLThElement", (Element,), {"tag": "th"})
thead = TagMeta("HTMLTheadElement", (Element,), {"tag": "thead"})
tr = TagMeta("HTMLTrElement", (Element,), {"tag": "tr"})

# Forms
button = TagMeta("HTMLButtonElement", (Element,), {"tag": "button"})
datalist = TagMeta("HTMLDatalistElement", (Element,), {"tag": "datalist"})
fieldset = TagMeta("HTMLFieldsetElement", (Element,), {"tag": "fieldset"})
form = TagMeta("HTMLFormElement", (Element,), {"tag": "form"})
input_ = TagMeta("HTMLInputElement", (VoidElement,), {"tag": "input"})
label = TagMeta("HTMLLabelElement", (Element,), {"tag": "label"})
legend = TagMeta("HTMLLegendElement", (Element,), {"tag": "legend"})
meter = TagMeta("HTMLMeterElement", (Element,), {"tag": "meter"})
optgroup = TagMeta("HTMLOptgroupElement", (Element,), {"tag": "optgroup"})
option = TagMeta("HTMLOptionElement", (Element,), {"tag": "option"})
output = TagMeta("HTMLOutputElement", (Element,), {"tag": "output"})
progress = TagMeta("HTMLProgressElement", (Element,), {"tag": "progress"})
select = TagMeta("HTMLSelectElement", (Element,), {"tag": "select"})
textarea = TagMeta("HTMLTextAreaElement", (Element,), {"tag": "textarea"})

# Interactive elements
details = TagMeta("HTMLDetailsElement", (Element,), {"tag": "details"})
dialog = TagMeta("HTMLDialogElement", (Element,), {"tag": "dialog"})
menu = TagMeta("HTMLMenuElement", (Element,), {"tag": "menu"})
summary = TagMeta("HTMLSummaryElement", (Element,), {"tag": "summary"})

# Web components
slot = TagMeta("HTMLSlotElement", (Element,), {"tag": "slot"})
template = TagMeta("HTMLTemplateElement", (Element,), {"tag": "template"})

__all__ = (
    "html",
    "head",
    "body",
    "base",
    "link",
    "meta",
    "style",
    "title",
    "address",
    "article",
    "aside",
    "footer",
    "header",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "main",
    "nav",
    "section",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "ul",
    "a",
    "abbr",
    "b",
    "bdi",
    "bdo",
    "br",
    "cite",
    "code",
    "data",
    "dfn",
    "em",
    "i",
    "kbd",
    "mark",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "time",
    "u",
    "var",
    "wbr",
    "del_",
    "ins",
    "area",
    "audio",
    "img",
    "map_",
    "track",
    "video",
    "embed",
    "iframe",
    "object_",
    "picture",
    "portal",
    "source",
    "canvas",
    "noscript",
    "script",
    "caption",
    "col",
    "colgroup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "button",
    "datalist",
    "fieldset",
    "form",
    "input_",
    "label",
    "legend",
    "meter",
    "optgroup",
    "option",
    "output",
    "progress",
    "select",
    "textarea",
    "details",
    "dialog",
    "menu",
    "summary",
    "slot",
    "template",
)
