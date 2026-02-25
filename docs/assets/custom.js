function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'uk',
        includedLanguages: 'uk,en,de,ko',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false // Strictly forbids the gray banner from appearing
    }, 'google_translate_element');
}

// === FONT SIZE CONTROL з збереженням у localStorage ===
const FONT_KEY = 'sbsq-font-size';
const FONT_MIN = 12;
const FONT_MAX = 28;
const FONT_DEFAULT = 16;

function applyFontSize(size) {
    document.documentElement.style.fontSize = size + 'px';
    localStorage.setItem(FONT_KEY, size);
    // Оновлюємо індикатор розміру якщо є
    const indicator = document.getElementById('font-size-indicator');
    if (indicator) indicator.textContent = size + 'px';
}

function changeSize(delta) {
    const saved = localStorage.getItem(FONT_KEY);
    const current = saved
        ? parseInt(saved)
        : parseInt(window.getComputedStyle(document.documentElement).fontSize) || FONT_DEFAULT;
    const newSize = Math.min(Math.max(current + delta, FONT_MIN), FONT_MAX);
    applyFontSize(newSize);
}

function resetFontSize() {
    applyFontSize(FONT_DEFAULT);
}

// Автоматично відновлюємо збережений розмір при кожному завантаженні сторінки
(function () {
    const saved = localStorage.getItem(FONT_KEY);
    if (saved) {
        document.documentElement.style.fontSize = parseInt(saved) + 'px';
    }
})();
