const hosts = {};
function findHost(name) {
    if (hosts[name]) return hosts[name];
    for (const el of document.querySelectorAll('*')) {
        if (el.shadowRoot) {
            const s = el.shadowRoot.querySelector('slot[name="' + name + '"]');
            if (s) { hosts[name] = el; return el; }
        }
    }
    return null;
}
function fill() {
    for (const el of [...document.body.children]) {
        const s = el.getAttribute('slot');
        if (!s) continue;
        const h = findHost(s);
        if (h && el.parentNode !== h) h.appendChild(el);
    }
}
new MutationObserver(fill).observe(document.body, { childList: true });
fill();
