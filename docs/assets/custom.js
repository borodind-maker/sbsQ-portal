// Custom JS for sbsQ Portal

document.addEventListener("DOMContentLoaded", function() {
    console.log("sbsQ Tactical Interface Loaded");

    // 1. Create Font Size Controls in Header
    function setupFontControls() {
        const headerTitle = document.querySelector(".md-header__topic");
        if (headerTitle && !document.querySelector(".font-controls")) {
            const controls = document.createElement("div");
            controls.className = "font-controls";
            
            const btnDecrease = document.createElement("button");
            btnDecrease.innerText = "A-";
            btnDecrease.className = "font-btn";
            btnDecrease.onclick = (e) => { e.preventDefault(); resizeFont(-1); };
            
            const btnIncrease = document.createElement("button");
            btnIncrease.innerText = "A+";
            btnIncrease.className = "font-btn";
            btnIncrease.onclick = (e) => { e.preventDefault(); resizeFont(1); };
            
            controls.appendChild(btnDecrease);
            controls.appendChild(btnIncrease);
            headerTitle.appendChild(controls);
            console.log("Font controls added to header");
        }
    }

    // 2. Fix Logo Link and Image
    function setupLogo() {
        const logoLink = document.querySelector(".md-header__button.md-logo");
        if (logoLink) {
            logoLink.href = "https://borodind-maker.github.io/sbsQ-portal/";
            logoLink.title = "Return to Main Portal";
            
            const img = logoLink.querySelector("img");
            if (img) {
                // Point to absolute path of logo
                img.src = "https://borodind-maker.github.io/sbsQ-portal/docs/assets/images/logo.png";
            }
        }
    }

    // Run initial setup
    setupFontControls();
    setupLogo();

    // Re-run setup if MkDocs dynamic navigation changes (sometimes needed for Single Page features)
    if (typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(() => {
            setupFontControls();
            setupLogo();
        });
        const header = document.querySelector('.md-header');
        if (header) observer.observe(header, { childList: true, subtree: true });
    }
});

let currentFontSize = 100; // Percentage

function resizeFont(delta) {
    currentFontSize += delta * 10;
    if (currentFontSize < 80) currentFontSize = 80;
    if (currentFontSize > 180) currentFontSize = 180;
    
    document.documentElement.style.fontSize = `${currentFontSize}%`;
    localStorage.setItem("sbs_font_scale", currentFontSize);
    console.log("Font resized to:", currentFontSize);
}

// Restore saved font size on load
(function() {
    const savedSize = localStorage.getItem("sbs_font_scale");
    if (savedSize) {
        document.documentElement.style.fontSize = `${savedSize}%`;
    }
})();
