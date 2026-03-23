# ⏩ ShiftHTML: an experimental HTML renderer

```python
from shifthtml import render, tags as t
from shifthtml.defer import defer

username = "Jane"
user_img = "https://example.com/photo.jpg"
todos = [
    "Invent new traffic lights",
    "Rehearse a movie scene",
    "Improve the spectrum technology",
]


def get_view_count() -> int:
    response = requests.get("https://example.com/count.json")
    return response.json()["count"]


page = (
    t.div()
    >> (
        t.h1() >> t"{username}'s Todos",
        t.img(src=user_img, alt=username, class_="photo"),
        t.ul() >> [t.li() >> todo for todo in todos],
        t.div()
        >> (
            t.span(class_="username") >> username,
            t.p() >> "lots of long text, blah blah",
        ),
        defer(
            "view-count",
            t.div() >> t"Slow to load count: {get_view_count}",
            loading=t.div() >> "Loading...",
        ),
        t.button(hx_post="/clicked", hx_swap="outerHTML") >> "Click me",
    )
)

html = "".join(render(page))
```
