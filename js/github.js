/* ============================================
   GITHUB INTEGRATION
   ============================================
   Fetches public repository statistics from
   GitHub API. Does NOT expose profile URLs
   or repository links in the frontend.

   Visitors must request links through the
   contact system.
   ============================================ */

const GITHUB_USERNAME = "ChristopherJohn1972";
const GITHUB_API = `https://api.github.com/users/${GITHUB_USERNAME}/repos`;

// Repositories to exclude from stats (forks, etc.)
const EXCLUDED_REPOS = [];

let allRepos = [];

async function fetchGitHubRepos() {
    const container = document.getElementById("githubRepos");

    try {
        const response = await fetch(`${GITHUB_API}?per_page=100&page=1&sort=updated`);

        if (response.status === 403) {
            // Rate limited — show partial data or fallback
            if (container) {
                container.innerHTML = '<p class="github__loading">GitHub rate limit reached. <a href="https://github.com/ChristopherJohn1972" target="_blank" style="color: var(--accent);">View profile directly.</a></p>';
            }
            renderFeaturedProjects();
            return;
        }

        if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);

        const repos = await response.json();
        allRepos = repos;

        // Update stats
        const repoCount = document.getElementById("repoCount");
        const totalStars = document.getElementById("totalStars");
        const totalLanguages = document.getElementById("totalLanguages");

        const filtered = repos.filter(r => !EXCLUDED_REPOS.includes(r.name));

        if (repoCount) repoCount.textContent = filtered.length;

        const stars = filtered.reduce((sum, r) => sum + (r.stargazers_count || 0), 0);
        if (totalStars) totalStars.textContent = stars;

        const languages = [...new Set(filtered.map(r => r.language).filter(Boolean))];
        if (totalLanguages) totalLanguages.textContent = languages.length;

        // Render repo cards (names and descriptions only — no URLs)
        if (container) {
            container.innerHTML = "";

            if (filtered.length === 0) {
                container.innerHTML = '<p class="github__loading">No repositories found.</p>';
                return;
            }

            // Sort by most recently updated
            const sorted = [...filtered].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

            // Show top repos
            const displayRepos = sorted.slice(0, 12);

            displayRepos.forEach(repo => {
                const card = createRepoCard(repo);
                container.appendChild(card);
            });

            if (sorted.length > 12) {
                const more = document.createElement("div");
                more.className = "repo-card";
                more.style.display = "flex";
                more.style.alignItems = "center";
                more.style.justifyContent = "center";
                more.style.color = "var(--accent)";
                more.style.cursor = "default";
                more.innerHTML = `<span style="font-size: 0.875rem; font-weight: 500;">+${sorted.length - 12} more repositories</span>`;
                container.appendChild(more);
            }
        }

        // Render featured projects
        renderFeaturedProjects();

    } catch (error) {
        console.error("Failed to fetch GitHub repos:", error);
        if (container) {
            container.innerHTML = '<p class="github__loading">Repository data unavailable. Request the full profile through the contact form.</p>';
        }
        renderFeaturedProjects();
    }
}

function createRepoCard(repo) {
    const card = document.createElement("div");
    card.className = "repo-card";

    card.innerHTML = `
        <div class="repo-card__name">${repo.name}</div>
        <p class="repo-card__desc">${repo.description || "No description provided."}</p>
    `;

    return card;
}

function renderFeaturedProjects() {
    const grid = document.getElementById("projectsGrid");
    if (!grid) return;

    grid.innerHTML = "";

    FEATURED_PROJECTS.forEach(project => {
        const card = createProjectCard(project);
        grid.appendChild(card);
    });
}

function createProjectCard(project) {
    const card = document.createElement("div");
    card.className = "project-card";
    card.setAttribute("data-category", project.category || "all");

    const statusClass = project.status === "Live" ? "live" : "development";

    // No URLs exposed — request links through contact form
    card.innerHTML = `
        <div class="project-card__header">
            <h3 class="project-card__name">${project.name}</h3>
            <span class="project-card__status project-card__status--${statusClass}">${project.status}</span>
        </div>
        <p class="project-card__description">${project.description}</p>
        <div class="project-card__tech">
            ${project.technologies.map(tech => `<span>${tech}</span>`).join("")}
        </div>
        <div class="project-card__features">
            ${project.features.map(feature => `<span>${feature}</span>`).join("")}
        </div>
    `;

    return card;
}
