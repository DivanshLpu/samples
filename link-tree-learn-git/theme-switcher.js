const themeLink = document.getElementById("theme-link");
const themeSelector = document.getElementById("theme");

function applyTheme(themeName) {
    themeLink.setAttribute("href", themeName);
    localStorage.setItem("theme", themeName);
}

themeSelector.addEventListener("change", (e) => {
    applyTheme(e.target.value);
});

const savedTheme = localStorage.getItem("theme");
if (savedTheme) {
    themeSelector.value = savedTheme;
    applyTheme(savedTheme);
}
