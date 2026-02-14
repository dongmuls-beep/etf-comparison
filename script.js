const GAS_API_URL = "./data.json";
const I18N_DIR = "./i18n";
const SUPPORTED_LANGS = ["ko", "vi", "zh", "en", "ja", "th", "tl", "km"];
const DEFAULT_LANG = "ko";

const i18nCache = new Map();

let allData = [];
let currentCategory = "";
let currentLanguage = DEFAULT_LANG;
let currentTranslations = {};
let lastFocusedBeforeModal = null;

let dataKeys = {
    category: "구분",
    code: "종목코드",
    name: "종목명",
    fee: "총보수",
    other: "기타비용",
    trade: "매매중개수수료",
    real: "실부담비용",
};

document.addEventListener("DOMContentLoaded", () => {
    void initApp();
});

async function initApp() {
    initNavigation();
    initModal();

    await initLanguage();
    await fetchData();
    handleRouting();

    window.addEventListener("hashchange", handleRouting);
}

async function initLanguage() {
    const selector = document.getElementById("languageSelect");
    const savedLang = localStorage.getItem("site_language");
    const browserLang = (navigator.language || DEFAULT_LANG).slice(0, 2).toLowerCase();

    const initialLang = SUPPORTED_LANGS.includes(savedLang)
        ? savedLang
        : (SUPPORTED_LANGS.includes(browserLang) ? browserLang : DEFAULT_LANG);

    if (selector) {
        selector.value = initialLang;
        selector.addEventListener("change", async (event) => {
            const value = event.target.value;
            await updateLanguage(value, { rerender: true });
        });
    }

    await updateLanguage(initialLang, { rerender: false });
}

async function loadLanguagePack(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) {
        return loadLanguagePack(DEFAULT_LANG);
    }

    if (i18nCache.has(lang)) {
        return i18nCache.get(lang);
    }

    try {
        const response = await fetch(`${I18N_DIR}/${lang}.json`, { cache: "no-store" });
        if (!response.ok) {
            throw new Error(`Failed to load language pack: ${lang}`);
        }

        const pack = await response.json();
        i18nCache.set(lang, pack);
        return pack;
    } catch (error) {
        if (lang !== DEFAULT_LANG) {
            return loadLanguagePack(DEFAULT_LANG);
        }
        console.error("Language pack loading failed:", error);
        return {};
    }
}

async function updateLanguage(lang, options = {}) {
    const { rerender = true } = options;
    const normalized = SUPPORTED_LANGS.includes(lang) ? lang : DEFAULT_LANG;
    const pack = await loadLanguagePack(normalized);

    currentLanguage = normalized;
    currentTranslations = pack;

    localStorage.setItem("site_language", currentLanguage);
    document.documentElement.lang = currentLanguage;

    applyTranslations();
    applySeoTranslations();

    const selector = document.getElementById("languageSelect");
    if (selector && selector.value !== currentLanguage) {
        selector.value = currentLanguage;
    }

    if (rerender && allData.length > 0) {
        renderTabs(allData);
        filterAndRenderTable();
        updateLastUpdated();
    }
}

function applyTranslations() {
    const targets = document.querySelectorAll("[data-i18n]");

    targets.forEach((el) => {
        const key = el.getAttribute("data-i18n");
        const translated = getTranslation(key);
        if (translated && translated !== key) {
            el.innerHTML = translated;
        }
    });
}

function applySeoTranslations() {
    const seoTitle = getTranslation("seo_title");
    const seoDescription = getTranslation("seo_description");

    if (seoTitle && seoTitle !== "seo_title") {
        document.title = seoTitle;

        const ogTitle = document.querySelector('meta[property="og:title"]');
        const twitterTitle = document.querySelector('meta[name="twitter:title"]');
        if (ogTitle) ogTitle.setAttribute("content", seoTitle);
        if (twitterTitle) twitterTitle.setAttribute("content", seoTitle);
    }

    if (seoDescription && seoDescription !== "seo_description") {
        const desc = document.querySelector('meta[name="description"]');
        const ogDesc = document.querySelector('meta[property="og:description"]');
        const twDesc = document.querySelector('meta[name="twitter:description"]');

        if (desc) desc.setAttribute("content", seoDescription);
        if (ogDesc) ogDesc.setAttribute("content", seoDescription);
        if (twDesc) twDesc.setAttribute("content", seoDescription);
    }
}

function getTranslation(key) {
    if (!key) return "";

    if (currentTranslations && key in currentTranslations) {
        return currentTranslations[key];
    }

    const koPack = i18nCache.get(DEFAULT_LANG);
    if (koPack && key in koPack) {
        return koPack[key];
    }

    return key;
}

function initNavigation() {
    const nav = document.getElementById("primaryNav");
    const hamburger = document.querySelector(".hamburger-menu");
    const navLinks = document.querySelectorAll(".nav-link");

    if (!nav || !hamburger) return;

    const closeNav = () => {
        nav.classList.remove("active");
        hamburger.classList.remove("active");
        hamburger.setAttribute("aria-expanded", "false");
        document.body.classList.remove("nav-open");
    };

    const openNav = () => {
        nav.classList.add("active");
        hamburger.classList.add("active");
        hamburger.setAttribute("aria-expanded", "true");
        document.body.classList.add("nav-open");
    };

    hamburger.addEventListener("click", () => {
        const isOpen = nav.classList.contains("active");
        if (isOpen) {
            closeNav();
        } else {
            openNav();
        }
    });

    navLinks.forEach((link) => {
        link.addEventListener("click", () => {
            closeNav();
        });
    });

    document.addEventListener("click", (event) => {
        if (!nav.classList.contains("active")) return;
        if (nav.contains(event.target) || hamburger.contains(event.target)) return;
        closeNav();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;

        const modal = document.getElementById("privacyModal");
        const isModalOpen = modal && !modal.hasAttribute("hidden");
        if (isModalOpen) {
            closePrivacyModal();
            return;
        }

        if (nav.classList.contains("active")) {
            closeNav();
        }
    });
}

function handleRouting() {
    const hash = window.location.hash || "#home";
    const cleanHash = hash.replace("#", "") || "home";
    const targetId = cleanHash === "home" ? "home-view" : `${cleanHash}-view`;

    const sections = document.querySelectorAll(".view-section");
    sections.forEach((section) => {
        section.classList.remove("active");
    });

    const target = document.getElementById(targetId) || document.getElementById("home-view");
    if (target) {
        target.classList.add("active");
    }

    const links = document.querySelectorAll(".nav-link");
    links.forEach((link) => {
        const href = link.getAttribute("href");
        link.classList.toggle("active", href === `#${cleanHash}` || (cleanHash === "home" && href === "#home"));
    });

    window.scrollTo({ top: 0, behavior: "auto" });
}

async function fetchData() {
    const tbody = document.getElementById("tableBody");

    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="6" class="loading-text">${getTranslation("table_loading")}</td></tr>`;
    updateLastUpdated(true);

    try {
        const response = await fetch(GAS_API_URL, { cache: "no-store" });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (!Array.isArray(data)) {
            throw new Error("Invalid data format");
        }

        allData = data;
        if (allData[0]) {
            resolveDataKeys(allData[0]);
        }

        renderTabs(allData);
        filterAndRenderTable();
        updateLastUpdated(false);
    } catch (error) {
        console.error("Error fetching data:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="loading-text error-text">${getTranslation("table_error")}</td></tr>`;
        updateLastUpdated(true);
    }
}

function resolveDataKeys(sample) {
    const keys = Object.keys(sample || {});
    if (keys.length === 0) return;

    const pick = (preferred, fallbacks, index) => {
        const exact = keys.find((key) => key === preferred);
        if (exact) return exact;

        const partial = keys.find((key) => fallbacks.some((fallback) => key.includes(fallback)));
        if (partial) return partial;

        return keys[index] || preferred;
    };

    dataKeys = {
        category: pick("구분", ["구분", "援"], 0),
        code: pick("종목코드", ["종목", "코드", "肄붾뱶"], 1),
        name: pick("종목명", ["종목명", "醫낅ぉ"], 2),
        fee: pick("총보수", ["총보수", "珥앸낫"], 3),
        other: pick("기타비용", ["기타", "鍮꾩슜"], 4),
        trade: pick("매매중개수수료", ["매매", "중개", "수수료", "?섏닔猷"], 5),
        real: pick("실부담비용", ["실부담", "?ㅻ??대퉬"], 6),
    };
}

function updateLastUpdated(isPending = false) {
    const lastUpdated = document.getElementById("lastUpdated");
    if (!lastUpdated) return;

    if (isPending) {
        lastUpdated.textContent = `${getTranslation("last_updated")}${"..."}`;
        return;
    }

    const now = new Date();
    const formatted = `${now.getFullYear()}/${String(now.getMonth() + 1).padStart(2, "0")}/${String(now.getDate()).padStart(2, "0")}`;
    lastUpdated.textContent = `${getTranslation("last_updated")} ${formatted}`;
}

function renderTabs(data) {
    const tabsContainer = document.getElementById("categoryTabs");
    if (!tabsContainer) return;

    const categories = [...new Set(
        data.map((item) => String(item[dataKeys.category] || "").trim()).filter(Boolean)
    )];

    tabsContainer.innerHTML = "";

    if (!currentCategory || !categories.includes(currentCategory)) {
        currentCategory = categories[0] || "";
    }

    categories.forEach((category) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = `tab-button ${category === currentCategory ? "active" : ""}`;
        button.dataset.category = category;
        button.textContent = category;

        button.addEventListener("click", () => {
            currentCategory = category;
            document.querySelectorAll(".tab-button").forEach((el) => {
                el.classList.toggle("active", el === button);
            });
            filterAndRenderTable();
            button.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
        });

        tabsContainer.appendChild(button);
    });
}

function filterAndRenderTable() {
    const normalizedCurrent = String(currentCategory || "").trim();
    const filtered = !normalizedCurrent
        ? allData
        : allData.filter((item) => String(item[dataKeys.category] || "").trim() === normalizedCurrent);

    renderTable(filtered);
}

function renderTable(rows) {
    const tbody = document.getElementById("tableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!rows || rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading-text">${getTranslation("table_empty")}</td></tr>`;
        return;
    }

    const sorted = [...rows].sort((a, b) => {
        const aValue = toNumber(a[dataKeys.real]);
        const bValue = toNumber(b[dataKeys.real]);
        return aValue - bValue;
    });

    sorted.forEach((item) => {
        const row = document.createElement("tr");

        const code = valueOrDash(item[dataKeys.code]);
        const name = valueOrDash(item[dataKeys.name]);
        const naverCode = code === "-" ? "" : String(code);
        const naverUrl = naverCode ? `https://finance.naver.com/item/main.naver?code=${encodeURIComponent(naverCode)}` : "#";

        row.innerHTML = `
            <td class="clickable code-cell" data-label="${escapeHtml(getTranslation("table_code"))}" title="Copy Code">${escapeHtml(code)}</td>
            <td data-label="${escapeHtml(getTranslation("table_name"))}" class="name-cell">
                <a href="${naverUrl}" target="_blank" rel="noopener noreferrer" class="stock-link">${escapeHtml(name)}</a>
            </td>
            <td class="text-right" data-label="${escapeHtml(getTranslation("table_fee"))}">${formatPercent(item[dataKeys.fee])}</td>
            <td class="text-right" data-label="${escapeHtml(getTranslation("table_other"))}">${formatPercent(item[dataKeys.other])}</td>
            <td class="text-right" data-label="${escapeHtml(getTranslation("table_trade"))}">${formatPercent(item[dataKeys.trade])}</td>
            <td class="text-right highlight" data-label="${escapeHtml(getTranslation("table_real"))}">${formatPercent(item[dataKeys.real])}</td>
        `;

        const codeCell = row.querySelector(".code-cell");
        if (codeCell && code !== "-") {
            codeCell.addEventListener("click", () => {
                void copyToClipboard(String(code));
            });
            codeCell.setAttribute("role", "button");
            codeCell.setAttribute("tabindex", "0");
            codeCell.addEventListener("keydown", (event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    void copyToClipboard(String(code));
                }
            });
        }

        tbody.appendChild(row);
    });
}

function toNumber(value) {
    if (value === null || value === undefined) return 0;

    const parsed = Number.parseFloat(String(value).replace(/,/g, "").replace(/%/g, ""));
    return Number.isFinite(parsed) ? parsed : 0;
}

function formatPercent(value) {
    const number = toNumber(value);
    return `${number.toFixed(4)}%`;
}

function valueOrDash(value) {
    if (value === null || value === undefined || String(value).trim() === "") {
        return "-";
    }
    return String(value);
}

function escapeHtml(raw) {
    return String(raw)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast(`Copied: ${text}`);
    } catch (error) {
        console.error("Copy failed:", error);
    }
}

function showToast(message) {
    let toast = document.getElementById("toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast";
        toast.className = "toast";
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.add("show");

    window.setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

function initModal() {
    const openLink = document.getElementById("privacyPolicyLink");
    const modal = document.getElementById("privacyModal");
    const closeBtn = document.getElementById("privacyModalClose");

    if (!openLink || !modal || !closeBtn) return;

    openLink.addEventListener("click", (event) => {
        event.preventDefault();
        openPrivacyModal();
    });

    closeBtn.addEventListener("click", () => {
        closePrivacyModal();
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closePrivacyModal();
        }
    });

    modal.addEventListener("keydown", handleModalFocusTrap);
}

function openPrivacyModal() {
    const modal = document.getElementById("privacyModal");
    const content = modal ? modal.querySelector(".modal-content") : null;
    if (!modal || !content) return;

    lastFocusedBeforeModal = document.activeElement instanceof HTMLElement ? document.activeElement : null;

    modal.removeAttribute("hidden");
    document.body.classList.add("modal-open");

    window.setTimeout(() => {
        content.focus();
    }, 0);
}

function closePrivacyModal() {
    const modal = document.getElementById("privacyModal");
    if (!modal) return;

    modal.setAttribute("hidden", "hidden");
    document.body.classList.remove("modal-open");

    if (lastFocusedBeforeModal) {
        lastFocusedBeforeModal.focus();
    }
}

function handleModalFocusTrap(event) {
    if (event.key === "Escape") {
        event.preventDefault();
        closePrivacyModal();
        return;
    }

    if (event.key !== "Tab") return;

    const modal = document.getElementById("privacyModal");
    if (!modal || modal.hasAttribute("hidden")) return;

    const focusable = modal.querySelectorAll(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
    );

    if (focusable.length === 0) {
        event.preventDefault();
        return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;

    if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
    }
}
