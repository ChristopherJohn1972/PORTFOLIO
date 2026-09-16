/* ============================================
   MAIN PORTFOLIO JAVASCRIPT
   ============================================
   Handles navigation, modals, forms,
   scroll effects, API submission,
   and anti-spam.
   ============================================ */

// Backend API base URL — auto-detects local vs production
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:')
    ? 'http://localhost:8000/api'
    : window.location.origin + '/api';

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initScrollEffects();
    initModals();
    initForms();
    fetchGitHubRepos();
    logPortfolioEvent('portfolio_visit', 'Portfolio accessed');
});

/* --- Event Logging --- */
function logPortfolioEvent(eventType, detail, endpoint) {
    try {
        fetch(`${API_BASE}/event/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_type: eventType,
                detail: detail || '',
                endpoint: endpoint || window.location.pathname,
            }),
        });
    } catch (e) { /* silent */ }
}

/* --- Navigation --- */
function initNavigation() {
    const toggle = document.getElementById("navToggle");
    const menu = document.getElementById("navMenu");
    const links = document.querySelectorAll(".nav__link");

    const overlay = document.createElement("div");
    overlay.className = "nav-overlay";
    document.body.appendChild(overlay);

    function closeMenu() {
        toggle.classList.remove("active");
        menu.classList.remove("active");
        overlay.classList.remove("active");
        document.body.style.overflow = "";
    }

    function openMenu() {
        toggle.classList.add("active");
        menu.classList.add("active");
        overlay.classList.add("active");
        document.body.style.overflow = "hidden";
    }

    toggle.addEventListener("click", () => {
        menu.classList.contains("active") ? closeMenu() : openMenu();
    });

    overlay.addEventListener("click", closeMenu);

    links.forEach(link => {
        link.addEventListener("click", closeMenu);
    });

    // Active link on scroll
    const sections = document.querySelectorAll("section[id]");

    function updateActiveLink() {
        const scrollY = window.scrollY + 100;
        sections.forEach(section => {
            const top = section.offsetTop - 100;
            const height = section.offsetHeight;
            const id = section.getAttribute("id");
            if (scrollY >= top && scrollY < top + height) {
                links.forEach(link => {
                    link.classList.remove("active");
                    if (link.getAttribute("href") === `#${id}`) {
                        link.classList.add("active");
                    }
                });
            }
        });
    }

    window.addEventListener("scroll", updateActiveLink, { passive: true });
    updateActiveLink();
}

/* --- Scroll Effects --- */
function initScrollEffects() {
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = "1";
                    entry.target.style.transform = "translateY(0)";
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    const animateElements = document.querySelectorAll(
        ".section__label, .section__title, .skill-group, .process__step, .cert-card, .experience__card, .education__card, .highlight-card, .project-card, .contact__action-card"
    );

    animateElements.forEach((el, i) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = `opacity 0.5s ease ${i * 0.05}s, transform 0.5s ease ${i * 0.05}s`;
        observer.observe(el);
    });

    const nav = document.getElementById("nav");
    window.addEventListener("scroll", () => {
        nav.style.background = window.scrollY > 50
            ? "rgba(10, 10, 15, 0.95)"
            : "rgba(10, 10, 15, 0.85)";
    }, { passive: true });
}

/* --- Modals --- */
function initModals() {
    document.querySelectorAll("[data-modal]").forEach(trigger => {
        trigger.addEventListener("click", (e) => {
            e.preventDefault();
            openModal(trigger.getAttribute("data-modal"));
        });
    });

    document.querySelectorAll(".modal__close").forEach(btn => {
        btn.addEventListener("click", () => {
            const modal = btn.closest(".modal-overlay");
            if (modal) closeModal(modal.id.replace("modal-", ""));
        });
    });

    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal(overlay.id.replace("modal-", ""));
        });
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            const active = document.querySelector(".modal-overlay.active");
            if (active) closeModal(active.id.replace("modal-", ""));
        }
    });

    document.querySelectorAll("[data-modal-close]").forEach(btn => {
        btn.addEventListener("click", () => {
            const modal = btn.closest(".modal-overlay");
            if (modal) {
                closeModal(modal.id.replace("modal-", ""));
                const target = btn.getAttribute("data-modal");
                if (target) setTimeout(() => openModal(target), 200);
            }
        });
    });
}

function openModal(id) {
    const overlay = document.getElementById(`modal-${id}`);
    if (!overlay) return;

    const form = overlay.querySelector("form");
    if (form) {
        form.reset();
        form.hidden = false;
    }

    const honeypot = overlay.querySelector(".form__honeypot");
    if (honeypot) honeypot.value = "";

    const success = overlay.querySelector(".modal__success");
    if (success) success.hidden = true;

    overlay.querySelectorAll(".form__error").forEach(el => el.textContent = "");
    overlay.querySelectorAll(".form__input.error, .conversational__input.error").forEach(el => el.classList.remove("error"));

    const convErrors = overlay.querySelector(".conversational__errors");
    if (convErrors) convErrors.textContent = "";

    overlay.classList.add("active");
    document.body.style.overflow = "hidden";

    setTimeout(() => {
        const first = overlay.querySelector("input:not([type=hidden]):not(.form__honeypot), select, textarea");
        if (first) first.focus();
    }, 300);
}

function closeModal(id) {
    const overlay = document.getElementById(`modal-${id}`);
    if (!overlay) return;
    overlay.classList.remove("active");
    document.body.style.overflow = "";
}

/* --- Forms --- */
function initForms() {
    const contactForm = document.getElementById("formContact");
    if (contactForm) {
        contactForm.addEventListener("submit", (e) => handleFormSubmit(e, "contact"));
        initConversationalOther("contact-type", "contactOtherWrap", "contact-other");
    }

    const cvForm = document.getElementById("formCv");
    if (cvForm) cvForm.addEventListener("submit", (e) => handleFormSubmit(e, "cv"));

    const projectsForm = document.getElementById("formProjects");
    if (projectsForm) projectsForm.addEventListener("submit", (e) => handleFormSubmit(e, "projects"));
}

function initConversationalOther(selectId, wrapId, otherInputId) {
    const select = document.getElementById(selectId);
    const wrap = document.getElementById(wrapId);
    const otherInput = document.getElementById(otherInputId);
    if (!select || !wrap) return;

    select.addEventListener("change", () => {
        if (select.value === "Other") {
            wrap.hidden = false;
            if (otherInput) otherInput.focus();
        } else {
            wrap.hidden = true;
            if (otherInput) otherInput.value = "";
        }
    });
}

/* --- Anti-Spam --- */
const submissionTimestamps = [];
const MAX_SUBMISSIONS = 3;
const TIME_WINDOW = 300000;

function checkRateLimit() {
    const now = Date.now();
    while (submissionTimestamps.length > 0 && submissionTimestamps[0] < now - TIME_WINDOW) {
        submissionTimestamps.shift();
    }
    return submissionTimestamps.length < MAX_SUBMISSIONS;
}

/* --- Form Handling --- */
async function handleFormSubmit(e, formType) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;

    // Honeypot check
    const honeypot = form.querySelector(".form__honeypot");
    if (honeypot && honeypot.value) {
        showSuccess(formType);
        return;
    }

    // Rate limit
    if (!checkRateLimit()) {
        alert("Too many submissions. Please try again later.");
        return;
    }

    // Validate
    if (!validateForm(form, formType)) return;

    // Disable button
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    // Collect data
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
        if (key === '_gotcha') return;
        if (key === 'opportunity_type_other') return;
        if (data[key]) {
            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        } else {
            data[key] = value;
        }
    });

    // If Other is selected, use the custom value as opportunity_type
    if (formType === 'contact' && data.opportunity_type === 'Other') {
        const otherInput = document.getElementById('contact-other');
        if (otherInput && otherInput.value.trim()) {
            data.opportunity_type = otherInput.value.trim();
        }
    }

    // Map form type to API endpoint
    const endpoints = {
        contact: '/contact/',
        cv: '/cv-request/',
        projects: '/project-links/',
    };

    try {
        const response = await fetch(`${API_BASE}${endpoints[formType]}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (response.ok) {
            submissionTimestamps.push(Date.now());
            showSuccess(formType);
        } else {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || 'Something went wrong. Please try again.';

            if (typeof errorMsg === 'object') {
                // Handle field errors
                const firstError = Object.values(errorMsg)[0];
                alert(Array.isArray(firstError) ? firstError[0] : errorMsg);
            } else {
                alert(errorMsg);
            }
        }
    } catch (err) {
        alert('Connection error. Please check your network and try again.');
        console.error('Form submission error:', err);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function validateForm(form, formType) {
    let valid = true;
    let errors = [];

    // Handle conversational form (contact)
    if (formType === "contact") {
        const requiredFields = form.querySelectorAll("[required]");
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                valid = false;
                field.classList.add("error");
                const label = field.getAttribute("data-label") || "this field";
                errors.push(label);
            } else {
                field.classList.remove("error");
            }
        });

        // Email validation
        const emailField = form.querySelector("input[type=email]");
        if (emailField && emailField.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(emailField.value)) {
                valid = false;
                emailField.classList.add("error");
                if (!errors.includes("email")) errors.push("a valid email");
            }
        }

        // Other specify validation
        const typeSelect = document.getElementById("contact-type");
        const otherInput = document.getElementById("contact-other");
        if (typeSelect && typeSelect.value === "Other") {
            if (!otherInput || !otherInput.value.trim()) {
                valid = false;
                if (otherInput) otherInput.classList.add("error");
                errors.push("specification for Other");
            } else {
                if (otherInput) otherInput.classList.remove("error");
            }
        }

        const errorEl = document.getElementById("conversationalErrors");
        if (errorEl) {
            errorEl.textContent = valid ? "" : "Please fill in: " + [...new Set(errors)].join(", ");
        }
        return valid;
    }

    // Standard form validation (cv, projects)
    const requiredFields = form.querySelectorAll("[required]");
    requiredFields.forEach(field => {
        const errorEl = field.parentElement.querySelector(".form__error");
        if (!field.value.trim()) {
            valid = false;
            field.classList.add("error");
            if (errorEl) errorEl.textContent = "This field is required.";
        } else {
            field.classList.remove("error");
            if (errorEl) errorEl.textContent = "";
        }
    });

    const emailField = form.querySelector("input[type=email]");
    if (emailField && emailField.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const errorEl = emailField.parentElement.querySelector(".form__error");
        if (!emailRegex.test(emailField.value)) {
            valid = false;
            emailField.classList.add("error");
            if (errorEl) errorEl.textContent = "Please enter a valid email address.";
        }
    }

    if (formType === "projects") {
        const checkboxes = form.querySelectorAll("input[name=projects]:checked");
        const errorEl = document.getElementById("proj-projects-error");
        if (checkboxes.length === 0) {
            valid = false;
            if (errorEl) errorEl.textContent = "Please select at least one project.";
        } else {
            if (errorEl) errorEl.textContent = "";
        }
    }

    return valid;
}

function showSuccess(formType) {
    const formId = {
        contact: 'formContact',
        cv: 'formCv',
        projects: 'formProjects',
    }[formType];

    const form = document.getElementById(formId);
    const success = document.getElementById(`success-${formType}`);

    if (form) form.hidden = true;
    if (success) success.hidden = false;
}
