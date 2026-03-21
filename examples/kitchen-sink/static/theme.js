const toggle = document.getElementById('theme-toggle');
toggle.addEventListener('click', () => {
  const root = document.documentElement;
  const isDark = root.style.colorScheme === 'dark';
  root.style.colorScheme = isDark ? 'light' : 'dark';
  toggle.textContent = isDark ? 'Dark Mode' : 'Light Mode';
});
