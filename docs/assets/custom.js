// Custom JS for sbsQ Portal - Tactical Version

document.addEventListener("DOMContentLoaded", function() {
    console.log("sbsQ Tactical Interface Loaded");

    // 1. Create Floating Tactical Font Controls
    function setupTacticalControls() {
        if (!document.querySelector(".font-controls")) {
            const controls = document.createElement("div");
            controls.className = "font-controls";
            
            const label = document.createElement("span");
            label.innerText = "ZOOM:";
            label.style.fontSize = "10px";
            label.style.color = "#8fde6d";
            label.style.marginRight = "5px";
            
            const btnDecrease = document.createElement("button");
            btnDecrease.innerText = "[-] ASC";
            btnDecrease.className = "font-btn";
            btnDecrease.onclick = () => resizeFont(-1);
            
            const btnIncrease = document.createElement("button");
            btnIncrease.innerText = "[+] DSC";
            btnIncrease.className = "font-btn";
            btnIncrease.onclick = () => resizeFont(1);
            
            controls.appendChild(label);
            controls.appendChild(btnDecrease);
            controls.appendChild(btnIncrease);
            document.body.appendChild(controls);
            console.log("Tactical font controls deployed");
        }
    }

    // 2. Fix Header Logo and Link
    function setupHeader() {
        const logo = document.querySelector(".md-logo");
        if (logo) {
            logo.href = "https://borodind-maker.github.io/sbsQ-portal/";
            const logoImg = logo.querySelector("img");
            if (logoImg) {
                logoImg.src = "https://borodind-maker.github.io/sbsQ-portal/docs/assets/images/logo.png";
            }
        }
    }

    setupTacticalControls();
    setupHeader();

    // Re-check after dynamic navigation
    const observer = new MutationObserver(() => {
        setupTacticalControls();
        setupHeader();
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

function resizeFont(delta) {
    let size = parseInt(localStorage.getItem("sbs_font_scale") || "100");
    size += delta * 15;
    if (size < 80) size = 80;
    if (size > 200) size = 200;
    
    document.documentElement.style.fontSize = `${size}%`;
    localStorage.setItem("sbs_font_scale", size);
}

// Global apply
(function() {
    const size = localStorage.getItem("sbs_font_scale") || "100";
    document.documentElement.style.fontSize = `${size}%`;
})();
