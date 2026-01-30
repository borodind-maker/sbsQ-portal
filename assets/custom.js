function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'uk',
        includedLanguages: 'uk,en,de,ko',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false // Strictly forbids the gray banner from appearing
    }, 'google_translate_element');
}

// Function to handle font scaling
function changeSize(delta) {
    const html = document.documentElement;
    let currentSize = parseInt(window.getComputedStyle(html).fontSize);
    // Limit scale between 12px and 24px
    let newSize = Math.min(Math.max(currentSize + delta, 12), 24);
    html.style.fontSize = newSize + "px";
}
