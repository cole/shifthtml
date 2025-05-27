# An experimental HTML renderer

```python
html = shift(
    h1 >> t"{username}'s Todos",
    img(src=user_img, alt=username, class="photo"),
    ul >> (
        li >> "Invent new traffic lights",
        li >> "Rehearse a movie scene",
        li >> "Improve the spectrum technology",
    ),
    div >> (
        span > {"class": "username"} >> username
        p >> "lots of long text, blah blah"
    ),
    button({"hx-post":"/clicked", "hx-swap": "outerHTML"}) >> "Click me"
)
```