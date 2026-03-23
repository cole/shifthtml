# ⏩ Shift: an experimental HTML renderer

```python
from shifthtml import button, div, h1, img, li, p, shift, span, ul
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


page = shift(
    div
    >> (
        h1 >> t"{username}'s Todos",
        img(src=user_img, alt=username, classname="photo"),
        ul >> [li >> todo for todo in todos],
        div >> (
            span(classname="username") >> username,
            p >> "lots of long text, blah blah",
        ),
        defer(
            "view-count",
            div >> t"Slow to load count: {get_view_count}",
            loading=div >> "Loading...",
        ),
        button(hx_post="/clicked", hx_swap="outerHTML") >> "Click me",
    )
)
```
