// Custom JS for sbsQ Portal - Tactical Version 3.0 (ULTIMATE GAME HUD)

document.addEventListener("DOMContentLoaded", function() {
    console.log("sbsQ Tactical Interface v3.0 Loaded");

    // 1. Create Floating Tactical Font Controls
    function setupTacticalControls() {
        if (!document.querySelector(".font-controls")) {
            const controls = document.createElement("div");
            controls.className = "font-controls";
            
            const btnDecrease = document.createElement("button");
            btnDecrease.innerText = "[-] ASC";
            btnDecrease.className = "font-btn";
            btnDecrease.onclick = () => resizeFont(-1);
            
            const btnIncrease = document.createElement("button");
            btnIncrease.innerText = "[+] DSC";
            btnIncrease.className = "font-btn";
            btnIncrease.onclick = () => resizeFont(1);
            
            controls.appendChild(btnDecrease);
            controls.appendChild(btnIncrease);
            document.body.appendChild(controls);
        }
    }

    // 2. Tactical Clock
    function updateClock() {
        const clockEl = document.getElementById('tactical-clock');
        if (clockEl) {
            const now = new Date();
            clockEl.innerText = now.toTimeString().split(' ')[0];
        }
    }
    setInterval(updateClock, 1000);

    // 3. Simulated Chat
    const chatStream = document.getElementById('chat-stream');
    const pilotNames = ['STALKER_ONE', 'BEE_MASTER', 'RESCUE_PILOT', 'GHOST_SWARM', 'ECHO_42'];
    const messages = [
        'Swarm 12 reporting for extraction.',
        'New artifacts detected in Sector-7.',
        'Does anyone have a spare Medkit?',
        'Testing Fibonacci pathing... feels smooth.',
        'Watch out for jamming in the north zone!',
        'License verified. Approaching terminal.'
    ];

    function addSimulatedMessage() {
        if (chatStream && Math.random() > 0.7) {
            const pilot = pilotNames[Math.floor(Math.random() * pilotNames.length)];
            const text = messages[Math.floor(Math.random() * messages.length)];
            
            const msgDiv = document.createElement('div');
            msgDiv.className = 'msg';
            msgDiv.innerHTML = `<span class="msg-pilot">${pilot}:</span> <span class="msg-text">${text}</span>`;
            chatStream.appendChild(msgDiv);
            chatStream.scrollTop = chatStream.scrollHeight;
            
            // Keep only last 15 messages
            if (chatStream.children.length > 15) chatStream.removeChild(chatStream.children[0]);
        }
    }
    setInterval(addSimulatedMessage, 3000);

    // Initial setups
    setupTacticalControls();
    updateClock();

    // Re-check after dynamic navigation
    const observer = new MutationObserver(() => {
        setupTacticalControls();
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

// Font Resizing Logic
function resizeFont(delta) {
    let size = parseInt(localStorage.getItem("sbs_font_scale") || "100");
    size += delta * 15;
    if (size < 70) size = 70;
    if (size > 220) size = 220;
    document.documentElement.style.fontSize = `${size}%`;
    localStorage.setItem("sbs_font_scale", size);
}

// Payment Interface Logic (Global for buttons)
window.openPayment = function(name, cost) {
    const modal = document.getElementById('payment-modal');
    document.getElementById('pay-item-name').innerText = name;
    document.getElementById('pay-item-cost').innerText = cost;
    modal.style.display = 'flex';
};

window.closePayment = function() {
    document.getElementById('payment-modal').style.display = 'none';
};

window.confirmPayment = function(method) {
    alert(`TRANSACTION AUTHORIZED [${method}]\nProcessing secure payment gateway...`);
    closePayment();
};

// Global font apply
(function() {
    const size = localStorage.getItem("sbs_font_scale") || "100";
    document.documentElement.style.fontSize = `${size}%`;
})();
