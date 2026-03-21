import random
from datetime import UTC, datetime
from time import sleep

from shifthtml import (
    Element,
    Lazy,
    a,
    abbr,
    address,
    article,
    aside,
    blockquote,
    body,
    br,
    button,
    caption,
    cite,
    code,
    dd,
    del_,
    details,
    div,
    dl,
    dt,
    em,
    fieldset,
    figcaption,
    figure,
    footer,
    form,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    head,
    header,
    hr,
    html,
    img,
    input_,
    ins,
    kbd,
    label,
    legend,
    li,
    link,
    main,
    mark,
    meta,
    nav,
    ol,
    option,
    p,
    pre,
    q,
    samp,
    script,
    section,
    select,
    small,
    strong,
    sub,
    summary,
    sup,
    table,
    tbody,
    td,
    textarea,
    th,
    title,
    tr,
    ul,
    var,
)
from shifthtml.defer import defer
from shifthtml.meta import TagMeta

hgroup = TagMeta("HTMLHGroupElement", (Element,), {"tag": "hgroup"})

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

    return html(lang="en") >> (
        page_head(),
        body
        >> (
            main
            >> (
                banner(now, request_count),
                hr,
                headings_section(),
                hr,
                nav_and_article_section(),
                hr,
                blockquote_section(),
                hr,
                dynamic_stats_section(now, request_count),
                hr,
                lazy_fortune_section(),
                hr,
                deferred_section(),
                hr,
                table_section(),
                hr,
                definition_list_section(),
                hr,
                lists_section(),
                hr,
                address_section(),
                hr,
                pre_section(),
                hr,
                figure_section(),
                hr,
                details_section(),
                hr,
                form_section(),
            ),
            script(src="/static/theme.js"),
        ),
    )


def page_head():
    return head >> (
        meta(charset="UTF-8"),
        meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        title >> "ShiftHTML Kitchen Sink",
        link(rel="icon", href="data:,"),
        link(rel="stylesheet", href="/static/style.css"),
    )


def banner(now: datetime, request_count: int):
    return div(classname="banner") >> (
        h1 >> "ShiftHTML Kitchen Sink",
        p >> f"Rendered server-side at {now:%Y-%m-%d %H:%M:%S UTC} · Request #{request_count}",
        p >> (button(id="theme-toggle") >> "Dark Mode",),
    )


def headings_section():
    return section >> (
        hgroup
        >> (
            h1 >> "h1 HTML5 Kitchen Sink",
            h2
            >> (
                "h2 Back in my quaint ",
                a(href="#") >> "garden",
            ),
            h3
            >> (
                "h3 Jaunty ",
                a(href="#") >> "zinnias",
                " vie with flaunting phlox",
            ),
            h4 >> "h4 Five or six big jet planes zoomed quickly by the new tower.",
            h5 >> "h5 Expect skilled signwriters to use many jazzy, quaint old alphabets effectively.",
            h6 >> "h6 Pack my box with five dozen liquor jugs.",
        ),
    )


def nav_and_article_section():
    nav_items = ["Home", "About", "Blog", "Projects", "Contact"]

    return section >> (
        header >> (nav >> (ul >> [li >> (a(href="#") >> item) for item in nav_items],),),
        article
        >> (
            p
            >> (
                "This paragraph is nested inside an article. It contains many different, sometimes useful, ",
                a(href="https://www.w3schools.com/tags/") >> "HTML5 tags",
                ". Of course there are classics like ",
                em >> "emphasis",
                ", ",
                strong >> "strong",
                ", and ",
                small >> "small",
                " but there are many others as well. Hover the following text for abbreviation tag: ",
                abbr(title="abbreviation") >> "abbr",
                ". You can define ",
                del_ >> "deleted text",
                " which often gets replaced with ",
                ins >> "inserted",
                " text.",
            ),
            p
            >> (
                "You can also use ",
                kbd >> "keyboard text",
                ", which sometimes is styled similarly to the ",
                code >> "<code>",
                " or ",
                samp >> "samp",
                " tags. Even more specifically, there is a tag just for ",
                var >> "variables",
                ". Not to be mistaken with blockquotes below, the quote tag lets you denote something as ",
                q >> "quoted text",
                ". Lastly don't forget the sub (H",
                sub >> "2",
                "O) and sup (E = MC",
                sup >> "2",
                ") tags.",
            ),
        ),
        aside >> "This is an aside.",
        footer >> "This is footer for this section",
    )


def blockquote_section():
    return section >> (
        blockquote >> (p >> "Blockquote: I quickly explained that many big jobs involve few hazards",),
        blockquote
        >> (
            p
            >> (
                "This is a multi-line blockquote with a cite reference. People think focus "
                "means saying yes to the thing you've got to focus on. But that's not what it "
                "means at all. It means saying no to the hundred other good ideas that there are. "
                "You have to pick carefully. I'm actually as proud of the things we haven't done "
                "as the things I have done. Innovation is saying no to 1,000 things.",
            ),
            cite >> "Steve Jobs \u2013 Apple Worldwide Developers' Conference, 1997",
        ),
    )


def dynamic_stats_section(now: datetime, request_count: int):
    cards = [
        ("Page Views", str(request_count)),
        ("Server Time", f"{now:%H:%M:%S}"),
        ("Python Version", "3.13"),
        ("Uptime", f"{now:%j} days into {now:%Y}"),
    ]

    return section >> (
        h2 >> "Dynamic Server Stats",
        div(classname="stats-grid")
        >> [
            div(classname="stat-card")
            >> (
                div(classname="value") >> value,
                div(classname="label") >> lbl,
            )
            for lbl, value in cards
        ],
    )


def lazy_fortune_section():
    """Lazy node: the fortune is selected at render time, not at tree-build time."""

    def pick_fortune():
        quote, author = random.choice(FORTUNES)
        return div(classname="fortune-box") >> (
            p
            >> (
                mark >> "Lazy node",
                " \u2014 evaluated at render time",
            ),
            p >> (em >> f"\u201c{quote}\u201d"),
            div(classname="attribution") >> f"\u2014 {author}",
        )

    return section >> (
        h2 >> "Lazy Fortune",
        Lazy(pick_fortune),
    )


def deferred_section():
    """Defer node: placeholder renders immediately, content swapped in via script at page end."""

    def slow_content():
        sleep(0.5)
        now = datetime.now(UTC)
        return div >> (
            p >> (strong >> "Deferred content loaded!"),
            p >> f"This was rendered 500ms after the initial page shell, at {now:%H:%M:%S.%f} UTC.",
            p
            >> (
                "The ",
                code >> "defer()",
                " plugin streams a placeholder first, then injects the real content via an inline ",
                code >> "<script>",
                " tag at the end of the response.",
            ),
        )

    return section >> (
        h2 >> "Deferred Content",
        defer(
            "slow-section",
            div(classname="deferred-box") >> slow_content,
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

    return section >> (
        table
        >> (
            caption >> "Tables can have captions now.",
            tbody
            >> [
                tr
                >> (
                    th >> "Person",
                    th >> "Number",
                    th >> "Third Column",
                ),
                *[
                    tr
                    >> (
                        td >> (a(href="#") >> name if i == 1 else name),
                        td >> str(num),
                        td >> desc,
                    )
                    for i, (name, num, desc) in enumerate(rows)
                ],
            ],
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

    return section >> (dl >> [item for term, desc in terms for item in (dt >> term, dd >> desc)],)


def lists_section():
    return section >> (
        ul
        >> (
            li
            >> (
                "Unordered List item one",
                ul
                >> (
                    li
                    >> (
                        "Nested list item",
                        ul
                        >> (
                            li >> "Level 3, item one",
                            li >> "Level 3, item two",
                            li >> "Level 3, item three",
                            li >> "Level 3, item four",
                        ),
                    ),
                    li >> "List item two",
                    li >> "List item three",
                    li >> "List item four",
                ),
            ),
            li >> "List item two",
            li >> "List item three",
            li >> "List item four",
        ),
        hr,
        ol
        >> (
            li
            >> (
                "List item one",
                ol
                >> (
                    li
                    >> (
                        "List item one",
                        ol
                        >> (
                            li >> "List item one",
                            li >> "List item two",
                            li >> "List item three",
                            li >> "List item four",
                        ),
                    ),
                    li >> "List item two",
                    li >> "List item three",
                    li >> "List item four",
                ),
            ),
            li >> "List item two",
            li >> "List item three",
            li >> "List item four",
        ),
    )


def address_section():
    return section >> (
        address
        >> (
            "1 Infinite Loop",
            br,
            "Cupertino, CA 95014",
            br,
            "United States",
        ),
    )


def pre_section():
    return section >> (
        pre
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
    return section >> (
        figure
        >> (
            img(
                src="https://picsum.photos/960/400",
                alt="A random photo from picsum.photos",
            ),
            figcaption
            >> (
                "Fig 1. A random image from ",
                a(href="https://picsum.photos/") >> "picsum.photos",
                " \u2014 refreshes each page load",
            ),
        ),
    )


def details_section():
    return section >> (
        details
        >> (
            summary >> "Click to expand this details element",
            p
            >> (
                "Here is some hidden content revealed by the ",
                code >> "<details>",
                " element. This is a great way to create collapsible sections without any JavaScript.",
            ),
        ),
        details(open=True)
        >> (
            summary >> "This one starts open",
            p
            >> (
                "The ",
                code >> "open",
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
    return section >> (
        form
        >> [
            *[
                p
                >> (
                    label({"for": field_id}) >> lbl,
                    input_(type=field_type, id=field_id, placeholder=placeholder),
                )
                for lbl, field_type, field_id, placeholder in INPUT_FIELDS
            ],
            p
            >> (
                label({"for": "example-input-range"}) >> "Range",
                input_(type="range", id="example-input-range", min="0", max="100", value="50"),
            ),
            p
            >> (
                label({"for": "example-select"}) >> "Example select",
                select(id="example-select") >> [option >> str(i) for i in range(1, 6)],
            ),
            p
            >> (
                label({"for": "example-select-multi"}) >> "Example multiple select",
                select(id="example-select-multi", multiple=True) >> [option >> str(i) for i in range(1, 6)],
            ),
            p
            >> (
                label({"for": "example-textarea"}) >> "Example textarea",
                textarea(id="example-textarea", rows="3"),
            ),
            p
            >> (
                label({"for": "example-input-file"}) >> "File input",
                input_(type="file", id="example-input-file"),
            ),
            fieldset
            >> (
                legend >> "I am legend",
                div
                >> (
                    label
                    >> (
                        input_(
                            type="radio",
                            name="options-radios",
                            id="options-radios-1",
                            value="option1",
                            checked=True,
                        ),
                        " Option one is this and that\u2014be sure to include why it's great",
                    ),
                ),
                div
                >> (
                    label
                    >> (
                        input_(
                            type="radio",
                            name="options-radios",
                            id="options-radios-2",
                            value="option2",
                        ),
                        " Option two can be something else and selecting it will deselect option one",
                    ),
                ),
                div
                >> (
                    label
                    >> (
                        input_(
                            type="radio",
                            name="options-radios",
                            id="options-radios-3",
                            value="option3",
                            disabled=True,
                        ),
                        " Option three is disabled",
                    ),
                ),
            ),
            fieldset
            >> (
                legend >> "I am also legend",
                label >> (input_(type="checkbox"), " Check me out"),
                label >> (input_(type="checkbox"), " Or check me out"),
            ),
            p
            >> (
                button(type="button") >> "Button",
                input_(type="button", value="Input Button"),
                input_(type="submit", value="Submit Button"),
                input_(type="reset", value="Reset Button"),
            ),
        ],
    )
