const links = [
    {
        label: "Projects",
        children: [
            { label: "Portfolio", url: "https://example.com/portfolio" },
            { label: "Open Source", url: "https://github.com" },
            { label: "Blog", url: "https://example.com/blog" }
        ]
    },
    {
        label: "Social",
        children: [
            { label: "Twitter / X", url: "https://x.com" },
            { label: "LinkedIn", url: "https://linkedin.com" },
            { label: "Instagram", url: "https://instagram.com" }
        ]
    },
    {
        label: "Contact",
        children: [
            { label: "Email", url: "mailto:hello@example.com" }
        ]
    },
    { label: "Website", url: "https://example.com" }
];

const tree = document.getElementById("tree");

function createLeaf(item) {
    const a = document.createElement("a");
    a.className = "leaf";
    a.href = item.url;
    a.textContent = item.label;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
}

function createBranch(item) {
    const branch = document.createElement("div");
    branch.className = "branch";

    const node = document.createElement("button");
    node.className = "node";
    node.type = "button";
    node.innerHTML = `<span>${item.label}</span>`;

    const chevron = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    chevron.setAttribute("class", "chevron");
    chevron.setAttribute("width", "18");
    chevron.setAttribute("height", "18");
    chevron.setAttribute("viewBox", "0 0 24 24");
    chevron.setAttribute("fill", "none");
    chevron.setAttribute("stroke", "currentColor");
    chevron.setAttribute("stroke-width", "2");
    chevron.setAttribute("stroke-linecap", "round");
    chevron.setAttribute("stroke-linejoin", "round");
    chevron.innerHTML = '<polyline points="9 18 15 12 9 6"></polyline>';
    node.appendChild(chevron);

    const childrenWrap = document.createElement("div");
    childrenWrap.className = "children";

    item.children.forEach((child) => {
        if (child.children) {
            childrenWrap.appendChild(createBranch(child));
        } else {
            childrenWrap.appendChild(createLeaf(child));
        }
    });

    node.addEventListener("click", () => {
        branch.classList.toggle("open");
        childrenWrap.style.maxHeight = branch.classList.contains("open")
            ? childrenWrap.scrollHeight + "px"
            : "0px";
    });

    branch.appendChild(node);
    branch.appendChild(childrenWrap);
    return branch;
}

function createLinkCard(item) {
    const a = document.createElement("a");
    a.className = "link-card";
    a.href = item.url;
    a.textContent = item.label;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
}

links.forEach((item) => {
    tree.appendChild(item.children ? createBranch(item) : createLinkCard(item));
});
