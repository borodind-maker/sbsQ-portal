// Custom JS for Font Resizing and Interactive Elements

document.addEventListener("DOMContentLoaded", function() {
    console.log("sbsQ Tactical Interface Loaded");

    // 1. Create Font Size Controls
    const header = document.querySelector(".md-header__topic");
    if (header) {
        const controls = document.createElement("div");
        controls.className = "font-controls";
        
        const btnDecrease = document.createElement("button");
        btnDecrease.innerText = "A-";
        btnDecrease.className = "font-btn";
        btnDecrease.onclick = () => resizeFont(-1);
        
        const btnIncrease = document.createElement("button");
        btnIncrease.innerText = "A+";
        btnIncrease.className = "font-btn";
        btnIncrease.onclick = () => resizeFont(1);
        
        controls.appendChild(btnDecrease);
        controls.appendChild(btnIncrease);
        
        header.appendChild(controls);
    }

    // 2. Fix Logo Link and Image
    const logoLink = document.querySelector(".md-header__button.md-logo");
    if (logoLink) {
        logoLink.href = "https://borodind-maker.github.io/sbsQ-portal/";
        logoLink.title = "Return to Main Portal";
        
        // Ensure image is correct if it exists
        const img = logoLink.querySelector("img");
        if (img) {
            img.src = "https://borodind-maker.github.io/sbsQ-portal/docs/assets/images/logo.png";
        }
    }
});

let currentFontSize = 100; // Percentage

function resizeFont(delta) {
    currentFontSize += delta * 10;
    // Limit range
    if (currentFontSize < 80) currentFontSize = 80;
    if (currentFontSize > 150) currentFontSize = 150;
    
    document.documentElement.style.fontSize = `${currentFontSize}%`;
    localStorage.setItem("sbs_font_scale", currentFontSize);
}

// Restore state
const savedSize = localStorage.getItem("sbs_font_scale");
if (savedSize) {
    currentFontSize = parseInt(savedSize);
    document.documentElement.style.fontSize = `${currentFontSize}%`;
}
