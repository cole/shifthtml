# ⏩ Shift: an experimental HTML renderer

```python

username = 'Jane'
user_img = 'https://example.com/photo.jpg
todos = [
    "Invent new traffic lights",
    "Rehearse a movie scene",
    "Improve the spectrum technology",
]


def get_view_count() -> int:
    response = requests.get("https://example.com/count.json")
    return response.json()["count"]


html = shift(
    h1 >> t"{username}'s Todos",
    img @ {"src": user_img, "alt": username, "class": "photo"},
    ul >> (li >> todo for todo in todos),
    div >> (
        span @ {"class": "username"} >> username
        p >> "lots of long text, blah blah"
    ),
    defer(
        "view-count",
        div >> t"Slow to load count: {get_view_count}"
        loading=(div >> "Loading...")
    )
    button(hx_post="/clicked", hx_swap="outerHTML") >> "Click me"
)
```
