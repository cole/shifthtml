import random
from datetime import UTC, datetime
from time import sleep

from shifthtml import Lazy
from shifthtml import tags as t
from shifthtml.defer import defer
from shifthtml.live import runtime

FORTUNES = [
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Any sufficiently advanced technology is indistinguishable from magic.", "Arthur C. Clarke"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Programs must be written for people to read.", "Hal Abelson"),
    (
        "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away.",
        "Antoine de Saint-Exupery",
    ),
]


def page(*, request_count: int):
    now = datetime.now(UTC)

    sections = (
        banner(now, request_count),
        t.hr(),
        headings_section(),
        t.hr(),
        nav_and_article_section(),
        t.hr(),
        blockquote_section(),
        t.hr(),
        dynamic_stats_section(now, request_count),
        t.hr(),
        lazy_fortune_section(),
        t.hr(),
        deferred_section(),
        t.hr(),
        table_section(),
        t.hr(),
        definition_list_section(),
        t.hr(),
        lists_section(),
        t.hr(),
        address_section(),
        t.hr(),
        pre_section(),
        t.hr(),
        figure_section(),
        t.hr(),
        details_section(),
        t.hr(),
        form_section(),
    )

    return t.html(lang="en") >> (
        page_head(),
        t.body() >> (t.main() >> sections, runtime(), t.script(src="/static/theme.js")),
    )


def page_head():
    return t.head() >> (
        t.meta(charset="UTF-8"),
        t.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        t.title() >> "ShiftHTML Kitchen Sink",
        t.link(rel="icon", href="data:,"),
        t.link(rel="stylesheet", href="/static/style.css"),
    )


def banner(now: datetime, request_count: int):
    return t.div(class_="banner") >> (
        t.h1() >> "ShiftHTML Kitchen Sink",
        t.p() >> f"Rendered server-side at {now:%Y-%m-%d %H:%M:%S UTC} · Request #{request_count}",
        t.p() >> (t.button(id="theme-toggle") >> "Dark Mode",),
    )


def headings_section():
    return t.section() >> (
        t.hgroup()
        >> (
            t.h1() >> "h1 HTML5 Kitchen Sink",
            t.h2() >> ("h2 Back in my quaint ", t.a(href="#") >> "garden"),
            t.h3() >> ("h3 Jaunty ", t.a(href="#") >> "zinnias", " vie with flaunting phlox"),
            t.h4() >> "h4 Five or six big jet planes zoomed quickly by the new tower.",
            t.h5() >> "h5 Expect skilled signwriters to use many jazzy, quaint old alphabets effectively.",
            t.h6() >> "h6 Pack my box with five dozen liquor jugs.",
        ),
    )


def nav_and_article_section():
    nav_items = ["Home", "About", "Blog", "Projects", "Contact"]
    nav_links = t.ul() >> [t.li() >> (t.a(href="#") >> item) for item in nav_items]

    inline_tags = t.p() >> (
        "This paragraph is nested inside an article. It contains many different, sometimes useful, ",
        t.a(href="https://www.w3schools.com/tags/") >> "HTML5 tags",
        ". Of course there are classics like ",
        t.em() >> "emphasis",
        ", ",
        t.strong() >> "strong",
        ", and ",
        t.small() >> "small",
        " but there are many others as well. Hover the following text for abbreviation tag: ",
        t.abbr(title="abbreviation") >> "abbr",
        ". You can define ",
        t.del_() >> "deleted text",
        " which often gets replaced with ",
        t.ins() >> "inserted",
        " text.",
    )

    more_tags = t.p() >> (
        "You can also use ",
        t.kbd() >> "keyboard text",
        ", which sometimes is styled similarly to the ",
        t.code() >> "<code>",
        " or ",
        t.samp() >> "samp",
        " tags. Even more specifically, there is a tag just for ",
        t.var() >> "variables",
        ". Not to be mistaken with blockquotes below, the quote tag lets you denote something as ",
        t.q() >> "quoted text",
        ". Lastly don't forget the sub (H",
        t.sub() >> "2",
        "O) and sup (E = MC",
        t.sup() >> "2",
        ") tags.",
    )

    return t.section() >> (
        t.header() >> (t.nav() >> (nav_links,)),
        t.article() >> (inline_tags, more_tags),
        t.aside() >> "This is an aside.",
        t.footer() >> "This is footer for this section",
    )


def blockquote_section():
    short_quote = t.blockquote() >> (t.p() >> "Blockquote: I quickly explained that many big jobs involve few hazards",)

    long_quote = t.blockquote() >> (
        t.p()
        >> (
            "This is a multi-line blockquote with a cite reference. People think focus "
            "means saying yes to the thing you've got to focus on. But that's not what it "
            "means at all. It means saying no to the hundred other good ideas that there are. "
            "You have to pick carefully. I'm actually as proud of the things we haven't done "
            "as the things I have done. Innovation is saying no to 1,000 things.",
        ),
        t.cite() >> "Steve Jobs \u2013 Apple Worldwide Developers' Conference, 1997",
    )

    return t.section() >> (short_quote, long_quote)


def dynamic_stats_section(now: datetime, request_count: int):
    cards = [
        ("Page Views", str(request_count)),
        ("Server Time", f"{now:%H:%M:%S}"),
        ("Python Version", "3.14"),
        ("Uptime", f"{now:%j} days into {now:%Y}"),
    ]

    stat_cards = [
        t.div(class_="stat-card")
        >> (
            t.div(class_="value") >> value,
            t.div(class_="label") >> lbl,
        )
        for lbl, value in cards
    ]

    return t.section() >> (
        t.h2() >> "Dynamic Server Stats",
        t.div(class_="stats-grid") >> stat_cards,
    )


def lazy_fortune_section():
    """Lazy node: the fortune is selected at render time, not at tree-build time."""

    def pick_fortune():
        quote, author = random.choice(FORTUNES)
        return t.div(class_="fortune-box") >> (
            t.p() >> (t.mark() >> "Lazy node", " \u2014 evaluated at render time"),
            t.p() >> (t.em() >> f"\u201c{quote}\u201d"),
            t.div(class_="attribution") >> f"\u2014 {author}",
        )

    return t.section() >> (
        t.h2() >> "Lazy Fortune",
        Lazy(pick_fortune),
    )


def deferred_section():
    """Defer node: placeholder renders immediately, content swapped in via <shift-update> at page end."""

    def slow_content():
        sleep(0.5)
        now = datetime.now(UTC)
        return t.div() >> (
            t.p() >> (t.strong() >> "Deferred content loaded!"),
            t.p() >> f"This was rendered 500ms after the initial page shell, at {now:%H:%M:%S.%f} UTC.",
            t.p()
            >> (
                "The ",
                t.code() >> "defer()",
                " plugin streams a placeholder first, then swaps in the real content via a ",
                t.code() >> "<shift-update>",
                " custom element at the end of the response.",
            ),
        )

    return t.section() >> (
        t.h2() >> "Deferred Content",
        defer(
            "slow-section",
            t.div(class_="deferred-box") >> slow_content,
            loading="Loading deferred content\u2026",
        ),
    )


def table_section():
    rows = [
        ("Someone Lastname", 900, "Nullam quis risus eget urna mollis ornare vel eu leo."),
        (
            "Person Name",
            1200,
            "Vestibulum id ligula porta felis euismod semper. Donec ullamcorper nulla non metus auctor fringilla.",
        ),
        ("Another Person", 1500, "Vivamus sagittis lacus vel augue laoreet rutrum faucibus dolor auctor."),
        ("Last One", 2800, "Morbi leo risus, porta ac consectetur ac, vestibulum at eros."),
    ]

    head_row = t.tr() >> (t.th() >> "Person", t.th() >> "Number", t.th() >> "Third Column")
    data_rows = [
        t.tr()
        >> (
            t.td() >> (t.a(href="#") >> name if i == 1 else name),
            t.td() >> str(num),
            t.td() >> desc,
        )
        for i, (name, num, desc) in enumerate(rows)
    ]

    return t.section() >> (
        t.table()
        >> (
            t.caption() >> "Tables can have captions now.",
            t.tbody() >> [head_row, *data_rows],
        ),
    )


def definition_list_section():
    terms = [
        ("Definition List Title", "Definition list division."),
        (
            "Kitchen Sink",
            "Used in expressions to describe work in which all conceivable "
            "(and some inconceivable) sources have been mined. In this case, a bunch of markup.",
        ),
        ("aside", "Defines content aside from the page content"),
        ("blockquote", "Defines a section that is quoted from another source"),
    ]

    return t.section() >> (t.dl() >> [item for term, desc in terms for item in (t.dt() >> term, t.dd() >> desc)],)


def lists_section():
    return t.section() >> (
        t.ul()
        >> (
            t.li()
            >> (
                "Unordered List item one",
                t.ul()
                >> (
                    t.li()
                    >> (
                        "Nested list item",
                        t.ul()
                        >> (
                            t.li() >> "Level 3, item one",
                            t.li() >> "Level 3, item two",
                            t.li() >> "Level 3, item three",
                            t.li() >> "Level 3, item four",
                        ),
                    ),
                    t.li() >> "List item two",
                    t.li() >> "List item three",
                    t.li() >> "List item four",
                ),
            ),
            t.li() >> "List item two",
            t.li() >> "List item three",
            t.li() >> "List item four",
        ),
        t.hr(),
        t.ol()
        >> (
            t.li()
            >> (
                "List item one",
                t.ol()
                >> (
                    t.li()
                    >> (
                        "List item one",
                        t.ol()
                        >> (
                            t.li() >> "List item one",
                            t.li() >> "List item two",
                            t.li() >> "List item three",
                            t.li() >> "List item four",
                        ),
                    ),
                    t.li() >> "List item two",
                    t.li() >> "List item three",
                    t.li() >> "List item four",
                ),
            ),
            t.li() >> "List item two",
            t.li() >> "List item three",
            t.li() >> "List item four",
        ),
    )


def address_section():
    return t.section() >> (
        t.address()
        >> (
            "1 Infinite Loop",
            t.br(),
            "Cupertino, CA 95014",
            t.br(),
            "United States",
        ),
    )


def pre_section():
    return t.section() >> (
        t.pre()
        >> (
            "pre {\n"
            "  display: block;\n"
            "  padding: 7px;\n"
            "  background-color: #F5F5F5;\n"
            "  border: 1px solid #E1E1E8;\n"
            "  border-radius: 3px;\n"
            "  white-space: pre-wrap;\n"
            "  word-break: break-all;\n"
            "  font-family: Menlo, Monaco;\n"
            "  line-height: 160%;\n"
            "}"
        ),
    )


def figure_section():
    return t.section() >> (
        t.figure()
        >> (
            t.img(
                src="https://picsum.photos/960/400",
                alt="A random photo from picsum.photos",
            ),
            t.figcaption()
            >> (
                "Fig 1. A random image from ",
                t.a(href="https://picsum.photos/") >> "picsum.photos",
                " \u2014 refreshes each page load",
            ),
        ),
    )


def details_section():
    return t.section() >> (
        t.details()
        >> (
            t.summary() >> "Click to expand this details element",
            t.p()
            >> (
                "Here is some hidden content revealed by the ",
                t.code() >> "<details>",
                " element. This is a great way to create collapsible sections without any JavaScript.",
            ),
        ),
        t.details(open=True)
        >> (
            t.summary() >> "This one starts open",
            t.p()
            >> (
                "The ",
                t.code() >> "open",
                " attribute makes this details element expanded by default.",
            ),
        ),
    )


INPUT_FIELDS = [
    ("Email address", "email", "example-input-email", "Enter email"),
    ("Number", "number", "example-input-number", "Number"),
    ("Password", "password", "example-input-password", "Password"),
    ("Search", "search", "example-input-search", "Search .."),
    ("Telephone number", "tel", "example-input-tel", "Telephone number"),
    ("Text", "text", "example-input-text", "Enter some text here"),
    ("Url", "url", "example-input-url", "Enter a url here"),
    ("Color", "color", "example-input-color", "#fff"),
    ("Date", "date", "example-input-date", "date"),
    ("Date / Time local", "datetime-local", "example-input-datetime-local", "date / time local"),
    ("Month", "month", "example-input-month", "Month"),
    ("Week", "week", "example-input-week", "Week"),
    ("Time", "time", "example-input-time", "Time"),
]


def form_section():
    text_fields = [
        t.p()
        >> (
            t.label({"for": field_id}) >> lbl,
            t.input_(type=field_type, id=field_id, placeholder=placeholder),
        )
        for lbl, field_type, field_id, placeholder in INPUT_FIELDS
    ]

    range_field = t.p() >> (
        t.label({"for": "example-input-range"}) >> "Range",
        t.input_(type="range", id="example-input-range", min="0", max="100", value="50"),
    )

    select_field = t.p() >> (
        t.label({"for": "example-select"}) >> "Example select",
        t.select(id="example-select") >> [t.option() >> str(i) for i in range(1, 6)],
    )

    multi_select = t.p() >> (
        t.label({"for": "example-select-multi"}) >> "Example multiple select",
        t.select(id="example-select-multi", multiple=True) >> [t.option() >> str(i) for i in range(1, 6)],
    )

    textarea_field = t.p() >> (
        t.label({"for": "example-textarea"}) >> "Example textarea",
        t.textarea(id="example-textarea", rows="3"),
    )

    file_field = t.p() >> (
        t.label({"for": "example-input-file"}) >> "File input",
        t.input_(type="file", id="example-input-file"),
    )

    radios = t.fieldset() >> (
        t.legend() >> "I am legend",
        t.div()
        >> (
            t.label()
            >> (
                t.input_(
                    type="radio",
                    name="options-radios",
                    id="options-radios-1",
                    value="option1",
                    checked=True,
                ),
                " Option one is this and that\u2014be sure to include why it's great",
            ),
        ),
        t.div()
        >> (
            t.label()
            >> (
                t.input_(
                    type="radio",
                    name="options-radios",
                    id="options-radios-2",
                    value="option2",
                ),
                " Option two can be something else and selecting it will deselect option one",
            ),
        ),
        t.div()
        >> (
            t.label()
            >> (
                t.input_(
                    type="radio",
                    name="options-radios",
                    id="options-radios-3",
                    value="option3",
                    disabled=True,
                ),
                " Option three is disabled",
            ),
        ),
    )

    checkboxes = t.fieldset() >> (
        t.legend() >> "I am also legend",
        t.label() >> (t.input_(type="checkbox"), " Check me out"),
        t.label() >> (t.input_(type="checkbox"), " Or check me out"),
    )

    buttons = t.p() >> (
        t.button(type="button") >> "Button",
        t.input_(type="button", value="Input Button"),
        t.input_(type="submit", value="Submit Button"),
        t.input_(type="reset", value="Reset Button"),
    )

    return t.section() >> (
        t.form()
        >> [
            *text_fields,
            range_field,
            select_field,
            multi_select,
            textarea_field,
            file_field,
            radios,
            checkboxes,
            buttons,
        ],
    )
