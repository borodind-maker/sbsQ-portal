function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'uk',
        includedLanguages: 'uk,en,de,ko',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
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

// Відновлюємо збережений розмір при кожному завантаженні
(function () {
    const saved = localStorage.getItem(FONT_KEY);
    if (saved) {
        document.documentElement.style.fontSize = parseInt(saved) + 'px';
    }
})();

// === ІНЖЕКЦІЯ КНОПОК A+/A- В ХЕДЕР MkDocs ===
// Надійний спосіб: додаємо кнопки в header через JS після завантаження DOM
document.addEventListener('DOMContentLoaded', function () {
    injectFontButtons();
});

// Для MkDocs Material з instant navigation — повторна інжекція при переходах
document.addEventListener('DOMContentSwitch', function () {
    injectFontButtons();
});

function injectFontButtons() {
    // Шукаємо вже вставлені кнопки — не дублюємо
    if (document.getElementById('sbsq-font-controls')) return;

    // Зона кнопок Material: .md-header__option або .md-header__inner
    const target = document.querySelector('.md-header__inner');
    if (!target) return;

    const savedSize = localStorage.getItem(FONT_KEY) || FONT_DEFAULT;

    const wrap = document.createElement('div');
    wrap.id = 'sbsq-font-controls';
    wrap.style.cssText = 'display:flex;align-items:center;gap:4px;margin-left:8px;';

    wrap.innerHTML = `
        <button onclick="changeSize(-2)" title="Зменшити шрифт"
            style="background:transparent;border:1px solid rgba(255,255,255,0.3);color:inherit;
                   border-radius:4px;padding:2px 7px;cursor:pointer;font-size:0.85rem;font-weight:bold;
                   line-height:1.4;">A<sup>−</sup></button>
        <span id="font-size-indicator" onclick="resetFontSize()" title="Скинути"
            style="font-size:0.65rem;cursor:pointer;opacity:0.6;min-width:30px;text-align:center;">${savedSize}px</span>
        <button onclick="changeSize(2)" title="Збільшити шрифт"
            style="background:transparent;border:1px solid rgba(255,255,255,0.3);color:inherit;
                   border-radius:4px;padding:2px 7px;cursor:pointer;font-size:1rem;font-weight:bold;
                   line-height:1.4;">A<sup>+</sup></button>
    `;

    // Вставляємо перед останнім елементом у хедері (перед search/settings)
    target.appendChild(wrap);
}
