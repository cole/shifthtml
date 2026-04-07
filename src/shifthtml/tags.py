from __future__ import annotations

from typing import ClassVar

from .element import Element, VoidElement
from .rendering import _collect_children

# -- Root --


class HTMLRootElement(Element):
    tag: ClassVar[str] = "html"
    doctype: ClassVar[str] = "<!DOCTYPE html>"

    def _collect(self, buf: list[str]) -> None:
        buf.append(self.doctype)
        super()._collect(buf)


class HTMLHeadElement(Element):
    tag: ClassVar[str] = "head"


class HTMLBodyElement(Element):
    tag: ClassVar[str] = "body"


# -- Metadata --


class HTMLBaseElement(VoidElement):
    tag: ClassVar[str] = "base"


class HTMLLinkElement(VoidElement):
    tag: ClassVar[str] = "link"


class HTMLMetaElement(VoidElement):
    tag: ClassVar[str] = "meta"


class HTMLStyleElement(Element):
    tag: ClassVar[str] = "style"


class HTMLTitleElement(Element):
    tag: ClassVar[str] = "title"


# -- Sectioning --


class HTMLAddressElement(Element):
    tag: ClassVar[str] = "address"


class HTMLArticleElement(Element):
    tag: ClassVar[str] = "article"


class HTMLAsideElement(Element):
    tag: ClassVar[str] = "aside"


class HTMLFooterElement(Element):
    tag: ClassVar[str] = "footer"


class HTMLHeaderElement(Element):
    tag: ClassVar[str] = "header"


class HTMLHGroupElement(Element):
    tag: ClassVar[str] = "hgroup"


class HTMLHeading1Element(Element):
    tag: ClassVar[str] = "h1"


class HTMLHeading2Element(Element):
    tag: ClassVar[str] = "h2"


class HTMLHeading3Element(Element):
    tag: ClassVar[str] = "h3"


class HTMLHeading4Element(Element):
    tag: ClassVar[str] = "h4"


class HTMLHeading5Element(Element):
    tag: ClassVar[str] = "h5"


class HTMLHeading6Element(Element):
    tag: ClassVar[str] = "h6"


class HTMLMainElement(Element):
    tag: ClassVar[str] = "main"


class HTMLNavElement(Element):
    tag: ClassVar[str] = "nav"


class HTMLSectionElement(Element):
    tag: ClassVar[str] = "section"


# -- Grouping content --


class HTMLBlockquoteElement(Element):
    tag: ClassVar[str] = "blockquote"


class HTMLDDElement(Element):
    tag: ClassVar[str] = "dd"


class HTMLDivElement(Element):
    tag: ClassVar[str] = "div"


class HTMLDLElement(Element):
    tag: ClassVar[str] = "dl"


class HTMLDTElement(Element):
    tag: ClassVar[str] = "dt"


class HTMLFigcaptionElement(Element):
    tag: ClassVar[str] = "figcaption"


class HTMLFigureElement(Element):
    tag: ClassVar[str] = "figure"


class HTMLHrElement(VoidElement):
    tag: ClassVar[str] = "hr"


class HTMLLiElement(Element):
    tag: ClassVar[str] = "li"


class HTMLOlElement(Element):
    tag: ClassVar[str] = "ol"


class HTMLParagraphElement(Element):
    tag: ClassVar[str] = "p"


class HTMLPreElement(Element):
    tag: ClassVar[str] = "pre"


class HTMLUlElement(Element):
    tag: ClassVar[str] = "ul"


# -- Text-level semantics --


class HTMLAnchorElement(Element):
    tag: ClassVar[str] = "a"


class HTMLAbbrElement(Element):
    tag: ClassVar[str] = "abbr"


class HTMLBoldElement(Element):
    tag: ClassVar[str] = "b"


class HTMLBdiElement(Element):
    tag: ClassVar[str] = "bdi"


class HTMLBdoElement(Element):
    tag: ClassVar[str] = "bdo"


class HTMLBRElement(VoidElement):
    tag: ClassVar[str] = "br"


class HTMLCiteElement(Element):
    tag: ClassVar[str] = "cite"


class HTMLCodeElement(Element):
    tag: ClassVar[str] = "code"


class HTMLDataElement(Element):
    tag: ClassVar[str] = "data"


class HTMLDfnElement(Element):
    tag: ClassVar[str] = "dfn"


class HTMLEmElement(Element):
    tag: ClassVar[str] = "em"


class HTMLItalicElement(Element):
    tag: ClassVar[str] = "i"


class HTMLKbdElement(Element):
    tag: ClassVar[str] = "kbd"


class HTMLMarkElement(Element):
    tag: ClassVar[str] = "mark"


class HTMLQuoteElement(Element):
    tag: ClassVar[str] = "q"


class HTMLRpElement(Element):
    tag: ClassVar[str] = "rp"


class HTMLRtElement(Element):
    tag: ClassVar[str] = "rt"


class HTMLRubyElement(Element):
    tag: ClassVar[str] = "ruby"


class HTMLSElement(Element):
    tag: ClassVar[str] = "s"


class HTMLSampElement(Element):
    tag: ClassVar[str] = "samp"


class HTMLSmallElement(Element):
    tag: ClassVar[str] = "small"


class HTMLSpanElement(Element):
    tag: ClassVar[str] = "span"


class HTMLStrongElement(Element):
    tag: ClassVar[str] = "strong"


class HTMLSubElement(Element):
    tag: ClassVar[str] = "sub"


class HTMLSupElement(Element):
    tag: ClassVar[str] = "sup"


class HTMLTimeElement(Element):
    tag: ClassVar[str] = "time"


class HTMLUElement(Element):
    tag: ClassVar[str] = "u"


class HTMLVarElement(Element):
    tag: ClassVar[str] = "var"


class HTMLWBRElement(VoidElement):
    tag: ClassVar[str] = "wbr"


# -- Edits --


class HTMLDelElement(Element):
    tag: ClassVar[str] = "del"


class HTMLInsElement(Element):
    tag: ClassVar[str] = "ins"


# -- Embedded content --


class HTMLAreaElement(VoidElement):
    tag: ClassVar[str] = "area"


class HTMLAudioElement(Element):
    tag: ClassVar[str] = "audio"


class HTMLImageElement(VoidElement):
    tag: ClassVar[str] = "img"


class HTMLMapElement(Element):
    tag: ClassVar[str] = "map"


class HTMLTrackElement(VoidElement):
    tag: ClassVar[str] = "track"


class HTMLVideoElement(Element):
    tag: ClassVar[str] = "video"


class HTMLEmbedElement(VoidElement):
    tag: ClassVar[str] = "embed"


class HTMLIFrameElement(Element):
    tag: ClassVar[str] = "iframe"


class HTMLObjectElement(Element):
    tag: ClassVar[str] = "object"


class HTMLPictureElement(Element):
    tag: ClassVar[str] = "picture"


class HTMLPortalElement(Element):
    tag: ClassVar[str] = "portal"


class HTMLSourceElement(VoidElement):
    tag: ClassVar[str] = "source"


# -- Scripting --


class HTMLCanvasElement(Element):
    tag: ClassVar[str] = "canvas"


class HTMLNoscriptElement(Element):
    tag: ClassVar[str] = "noscript"


class HTMLScriptElement(Element):
    tag: ClassVar[str] = "script"


# -- Table content --


class HTMLCaptionElement(Element):
    tag: ClassVar[str] = "caption"


class HTMLColElement(VoidElement):
    tag: ClassVar[str] = "col"


class HTMLColgroupElement(Element):
    tag: ClassVar[str] = "colgroup"


class HTMLTableElement(Element):
    tag: ClassVar[str] = "table"


class HTMLTbodyElement(Element):
    tag: ClassVar[str] = "tbody"


class HTMLTdElement(Element):
    tag: ClassVar[str] = "td"


class HTMLTfootElement(Element):
    tag: ClassVar[str] = "tfoot"


class HTMLThElement(Element):
    tag: ClassVar[str] = "th"


class HTMLTheadElement(Element):
    tag: ClassVar[str] = "thead"


class HTMLTrElement(Element):
    tag: ClassVar[str] = "tr"


# -- Forms --


class HTMLButtonElement(Element):
    tag: ClassVar[str] = "button"


class HTMLDatalistElement(Element):
    tag: ClassVar[str] = "datalist"


class HTMLFieldsetElement(Element):
    tag: ClassVar[str] = "fieldset"


class HTMLFormElement(Element):
    tag: ClassVar[str] = "form"


class HTMLInputElement(VoidElement):
    tag: ClassVar[str] = "input"


class HTMLLabelElement(Element):
    tag: ClassVar[str] = "label"


class HTMLLegendElement(Element):
    tag: ClassVar[str] = "legend"


class HTMLMeterElement(Element):
    tag: ClassVar[str] = "meter"


class HTMLOptgroupElement(Element):
    tag: ClassVar[str] = "optgroup"


class HTMLOptionElement(Element):
    tag: ClassVar[str] = "option"


class HTMLOutputElement(Element):
    tag: ClassVar[str] = "output"


class HTMLProgressElement(Element):
    tag: ClassVar[str] = "progress"


class HTMLSelectElement(Element):
    tag: ClassVar[str] = "select"


class HTMLTextAreaElement(Element):
    tag: ClassVar[str] = "textarea"


# -- Interactive elements --


class HTMLDetailsElement(Element):
    tag: ClassVar[str] = "details"


class HTMLDialogElement(Element):
    tag: ClassVar[str] = "dialog"


class HTMLMenuElement(Element):
    tag: ClassVar[str] = "menu"


class HTMLSummaryElement(Element):
    tag: ClassVar[str] = "summary"


# -- Web components --


class HTMLSlotElement(Element):
    tag: ClassVar[str] = "slot"


class HTMLTemplateElement(Element):
    tag: ClassVar[str] = "template"


# -- Lowercase aliases --

html = HTMLRootElement
head = HTMLHeadElement
body = HTMLBodyElement
base = HTMLBaseElement
link = HTMLLinkElement
meta = HTMLMetaElement
style = HTMLStyleElement
title = HTMLTitleElement
address = HTMLAddressElement
article = HTMLArticleElement
aside = HTMLAsideElement
footer = HTMLFooterElement
header = HTMLHeaderElement
hgroup = HTMLHGroupElement
h1 = HTMLHeading1Element
h2 = HTMLHeading2Element
h3 = HTMLHeading3Element
h4 = HTMLHeading4Element
h5 = HTMLHeading5Element
h6 = HTMLHeading6Element
main = HTMLMainElement
nav = HTMLNavElement
section = HTMLSectionElement
blockquote = HTMLBlockquoteElement
dd = HTMLDDElement
div = HTMLDivElement
dl = HTMLDLElement
dt = HTMLDTElement
figcaption = HTMLFigcaptionElement
figure = HTMLFigureElement
hr = HTMLHrElement
li = HTMLLiElement
ol = HTMLOlElement
p = HTMLParagraphElement
pre = HTMLPreElement
ul = HTMLUlElement
a = HTMLAnchorElement
abbr = HTMLAbbrElement
b = HTMLBoldElement
bdi = HTMLBdiElement
bdo = HTMLBdoElement
br = HTMLBRElement
cite = HTMLCiteElement
code = HTMLCodeElement
data = HTMLDataElement
dfn = HTMLDfnElement
em = HTMLEmElement
i = HTMLItalicElement
kbd = HTMLKbdElement
mark = HTMLMarkElement
q = HTMLQuoteElement
rp = HTMLRpElement
rt = HTMLRtElement
ruby = HTMLRubyElement
s = HTMLSElement
samp = HTMLSampElement
small = HTMLSmallElement
span = HTMLSpanElement
strong = HTMLStrongElement
sub = HTMLSubElement
sup = HTMLSupElement
time = HTMLTimeElement
u = HTMLUElement
var = HTMLVarElement
wbr = HTMLWBRElement
del_ = HTMLDelElement
ins = HTMLInsElement
area = HTMLAreaElement
audio = HTMLAudioElement
img = HTMLImageElement
map_ = HTMLMapElement
track = HTMLTrackElement
video = HTMLVideoElement
embed = HTMLEmbedElement
iframe = HTMLIFrameElement
object_ = HTMLObjectElement
picture = HTMLPictureElement
portal = HTMLPortalElement
source = HTMLSourceElement
canvas = HTMLCanvasElement
noscript = HTMLNoscriptElement
script = HTMLScriptElement
caption = HTMLCaptionElement
col = HTMLColElement
colgroup = HTMLColgroupElement
table = HTMLTableElement
tbody = HTMLTbodyElement
td = HTMLTdElement
tfoot = HTMLTfootElement
th = HTMLThElement
thead = HTMLTheadElement
tr = HTMLTrElement
button = HTMLButtonElement
datalist = HTMLDatalistElement
fieldset = HTMLFieldsetElement
form = HTMLFormElement
input_ = HTMLInputElement
label = HTMLLabelElement
legend = HTMLLegendElement
meter = HTMLMeterElement
optgroup = HTMLOptgroupElement
option = HTMLOptionElement
output = HTMLOutputElement
progress = HTMLProgressElement
select = HTMLSelectElement
textarea = HTMLTextAreaElement
details = HTMLDetailsElement
dialog = HTMLDialogElement
menu = HTMLMenuElement
summary = HTMLSummaryElement
slot = HTMLSlotElement
template = HTMLTemplateElement

__all__ = (
    # Class names
    "HTMLRootElement",
    "HTMLHeadElement",
    "HTMLBodyElement",
    "HTMLBaseElement",
    "HTMLLinkElement",
    "HTMLMetaElement",
    "HTMLStyleElement",
    "HTMLTitleElement",
    "HTMLAddressElement",
    "HTMLArticleElement",
    "HTMLAsideElement",
    "HTMLFooterElement",
    "HTMLHeaderElement",
    "HTMLHGroupElement",
    "HTMLHeading1Element",
    "HTMLHeading2Element",
    "HTMLHeading3Element",
    "HTMLHeading4Element",
    "HTMLHeading5Element",
    "HTMLHeading6Element",
    "HTMLMainElement",
    "HTMLNavElement",
    "HTMLSectionElement",
    "HTMLBlockquoteElement",
    "HTMLDDElement",
    "HTMLDivElement",
    "HTMLDLElement",
    "HTMLDTElement",
    "HTMLFigcaptionElement",
    "HTMLFigureElement",
    "HTMLHrElement",
    "HTMLLiElement",
    "HTMLOlElement",
    "HTMLParagraphElement",
    "HTMLPreElement",
    "HTMLUlElement",
    "HTMLAnchorElement",
    "HTMLAbbrElement",
    "HTMLBoldElement",
    "HTMLBdiElement",
    "HTMLBdoElement",
    "HTMLBRElement",
    "HTMLCiteElement",
    "HTMLCodeElement",
    "HTMLDataElement",
    "HTMLDfnElement",
    "HTMLEmElement",
    "HTMLItalicElement",
    "HTMLKbdElement",
    "HTMLMarkElement",
    "HTMLQuoteElement",
    "HTMLRpElement",
    "HTMLRtElement",
    "HTMLRubyElement",
    "HTMLSElement",
    "HTMLSampElement",
    "HTMLSmallElement",
    "HTMLSpanElement",
    "HTMLStrongElement",
    "HTMLSubElement",
    "HTMLSupElement",
    "HTMLTimeElement",
    "HTMLUElement",
    "HTMLVarElement",
    "HTMLWBRElement",
    "HTMLDelElement",
    "HTMLInsElement",
    "HTMLAreaElement",
    "HTMLAudioElement",
    "HTMLImageElement",
    "HTMLMapElement",
    "HTMLTrackElement",
    "HTMLVideoElement",
    "HTMLEmbedElement",
    "HTMLIFrameElement",
    "HTMLObjectElement",
    "HTMLPictureElement",
    "HTMLPortalElement",
    "HTMLSourceElement",
    "HTMLCanvasElement",
    "HTMLNoscriptElement",
    "HTMLScriptElement",
    "HTMLCaptionElement",
    "HTMLColElement",
    "HTMLColgroupElement",
    "HTMLTableElement",
    "HTMLTbodyElement",
    "HTMLTdElement",
    "HTMLTfootElement",
    "HTMLThElement",
    "HTMLTheadElement",
    "HTMLTrElement",
    "HTMLButtonElement",
    "HTMLDatalistElement",
    "HTMLFieldsetElement",
    "HTMLFormElement",
    "HTMLInputElement",
    "HTMLLabelElement",
    "HTMLLegendElement",
    "HTMLMeterElement",
    "HTMLOptgroupElement",
    "HTMLOptionElement",
    "HTMLOutputElement",
    "HTMLProgressElement",
    "HTMLSelectElement",
    "HTMLTextAreaElement",
    "HTMLDetailsElement",
    "HTMLDialogElement",
    "HTMLMenuElement",
    "HTMLSummaryElement",
    "HTMLSlotElement",
    "HTMLTemplateElement",
    # Lowercase aliases
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
    "hgroup",
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
