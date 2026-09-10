/**
 * CineMatch AI — Modern Client-Side JavaScript
 * Handles real-time autocomplete, recommendation lookups, genre filtering,
 * movie detail modals, and keyboard navigation.
 */

let currentPage = 1;
let currentGenre = "";
let currentQuery = "";
let debounceTimer = null;
let selectedAutoIndex = -1;

document.addEventListener("DOMContentLoaded", () => {
  initSearch();
  initGenreFilters();
  initModal();
  initKeyboardShortcuts();
});

/* ==========================================================================
   Search & Autocomplete
   ========================================================================== */
function initSearch() {
  const input = document.getElementById("searchInput");
  const dropdown = document.getElementById("autocompleteList");
  const clearBtn = document.getElementById("clearSearchBtn");

  if (!input) return;

  input.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    if (clearBtn) clearBtn.style.display = val ? "block" : "none";

    clearTimeout(debounceTimer);
    if (!val) {
      dropdown.style.display = "none";
      dropdown.innerHTML = "";
      return;
    }

    debounceTimer = setTimeout(() => {
      fetchAutocomplete(val);
    }, 200);
  });

  input.addEventListener("keydown", (e) => {
    const items = dropdown.querySelectorAll(".autocomplete-item");
    if (!items.length || dropdown.style.display === "none") {
      if (e.key === "Enter") {
        performSearch(input.value.trim());
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      selectedAutoIndex = (selectedAutoIndex + 1) % items.length;
      updateAutoSelection(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      selectedAutoIndex = (selectedAutoIndex - 1 + items.length) % items.length;
      updateAutoSelection(items);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedAutoIndex >= 0 && items[selectedAutoIndex]) {
        items[selectedAutoIndex].click();
      } else {
        performSearch(input.value.trim());
      }
    } else if (e.key === "Escape") {
      dropdown.style.display = "none";
    }
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      input.value = "";
      clearBtn.style.display = "none";
      dropdown.style.display = "none";
      currentQuery = "";
      resetExploreSection();
    });
  }

  // Close dropdown on outside click
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-wrapper")) {
      dropdown.style.display = "none";
    }
  });
}

function updateAutoSelection(items) {
  items.forEach((item, idx) => {
    if (idx === selectedAutoIndex) {
      item.classList.add("selected");
      item.scrollIntoView({ block: "nearest" });
    } else {
      item.classList.remove("selected");
    }
  });
}

async function fetchAutocomplete(query) {
  const dropdown = document.getElementById("autocompleteList");
  try {
    const res = await fetch(`/api/autocomplete?q=${encodeURIComponent(query)}`);
    if (!res.ok) return;
    const data = await res.json();

    if (!data || data.length === 0) {
      dropdown.innerHTML = `<div style="padding: 14px 18px; color: var(--text-dim); font-size: 0.85rem;">No matching films found.</div>`;
      dropdown.style.display = "block";
      return;
    }

    selectedAutoIndex = -1;
    dropdown.innerHTML = data.map(item => `
      <div class="autocomplete-item" onclick="selectMovieFromSearch(${item.id}, '${escapeQuotes(item.title)}')">
        <img src="${item.poster_url}" alt="${escapeQuotes(item.title)}" class="auto-thumb" onerror="this.src='/static/img/placeholder.svg'">
        <div class="auto-info">
          <div class="auto-title">${item.title}</div>
          <div class="auto-meta">
            <span>${item.release_year || 'N/A'}</span>
            <span>★ ${item.vote_average || '0.0'}</span>
            <span>${(item.genres || []).join(', ')}</span>
          </div>
        </div>
        <span class="auto-action">Recommend &rarr;</span>
      </div>
    `).join("");

    dropdown.style.display = "block";
  } catch (err) {
    console.error("Autocomplete error:", err);
  }
}

function selectMovieFromSearch(movieId, title) {
  document.getElementById("autocompleteList").style.display = "none";
  recommendMovie(movieId, title);
}

function performSearch(query) {
  document.getElementById("autocompleteList").style.display = "none";
  currentQuery = query;
  currentPage = 1;
  fetchMoviesList(true);
}

/* ==========================================================================
   Genre Filters
   ========================================================================== */
function initGenreFilters() {
  const container = document.getElementById("genreChipsContainer");
  if (!container) return;

  container.addEventListener("click", (e) => {
    const chip = e.target.closest(".genre-chip");
    if (!chip) return;

    container.querySelectorAll(".genre-chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");

    currentGenre = chip.getAttribute("data-genre") || "";
    currentPage = 1;
    fetchMoviesList(true);
  });
}

/* ==========================================================================
   Movies Grid Fetcher & Renderer
   ========================================================================== */
async function fetchMoviesList(reset = false) {
  const grid = document.getElementById("moviesGrid");
  const loadMoreBtn = document.getElementById("loadMoreBtn");
  const countLabel = document.getElementById("resultsCountLabel");
  const titleElem = document.getElementById("exploreSectionTitle");
  const subtitleElem = document.getElementById("exploreSectionSubtitle");

  let url = `/api/movies?page=${currentPage}&page_size=24`;
  if (currentQuery) url += `&q=${encodeURIComponent(currentQuery)}`;
  if (currentGenre) url += `&genre=${encodeURIComponent(currentGenre)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch movies");
    const data = await res.json();

    // Update headings
    if (currentQuery) {
      titleElem.innerHTML = `Search results for "<span class="gradient-text">${currentQuery}</span>"`;
      subtitleElem.textContent = `Found ${data.total} matching titles in the catalog.`;
    } else if (currentGenre) {
      titleElem.textContent = `${currentGenre} Movies`;
      subtitleElem.textContent = `Browsing ${data.total} films categorized under ${currentGenre}.`;
    } else {
      titleElem.textContent = "Explore Cinema Library";
      subtitleElem.textContent = `Showing all films from the TMDB 5000 catalog.`;
    }

    if (countLabel) {
      const shownCount = (currentPage - 1) * 24 + data.results.length;
      countLabel.textContent = `Showing ${shownCount} of ${data.total} movies`;
    }

    const cardsHtml = data.results.map(m => createMovieCardHtml(m)).join("");

    if (reset) {
      grid.innerHTML = cardsHtml;
    } else {
      grid.insertAdjacentHTML("beforeend", cardsHtml);
    }

    // Toggle Load More button
    if (loadMoreBtn) {
      const hasMore = (currentPage * 24) < data.total;
      loadMoreBtn.style.display = hasMore ? "inline-flex" : "none";
    }
  } catch (err) {
    console.error("Error loading movies:", err);
  }
}

function loadMoreMovies() {
  currentPage += 1;
  fetchMoviesList(false);
}

function resetExploreSection() {
  currentQuery = "";
  currentGenre = "";
  currentPage = 1;
  const container = document.getElementById("genreChipsContainer");
  if (container) {
    container.querySelectorAll(".genre-chip").forEach(c => c.classList.remove("active"));
    const firstChip = container.querySelector(".genre-chip");
    if (firstChip) firstChip.classList.add("active");
  }
  fetchMoviesList(true);
}

function createMovieCardHtml(movie, matchScore = null) {
  const firstGenre = movie.genres && movie.genres.length ? movie.genres[0] : "Cinema";
  const matchHtml = matchScore ? `<span class="match-pill">${matchScore}% MATCH</span>` : "";

  return `
    <div class="movie-card" data-movie-id="${movie.id}">
      <div class="card-poster-wrapper">
        ${matchHtml}
        <img 
          src="${movie.poster_url}" 
          alt="${escapeQuotes(movie.title)}" 
          class="card-poster"
          loading="lazy"
          onerror="this.src='/static/img/placeholder.svg'"
        >
        <div class="card-overlay">
          <button class="card-action-btn primary" title="Recommend Similar" onclick="recommendMovie(${movie.id}, '${escapeQuotes(movie.title)}')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path>
            </svg>
            Recommend
          </button>
          <button class="card-action-btn secondary" title="Movie Info" onclick="openMovieModal(${movie.id})">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            Info
          </button>
        </div>
        <span class="card-rating">★ ${movie.vote_average || '0.0'}</span>
      </div>
      <div class="card-info">
        <h4 class="card-title" title="${escapeQuotes(movie.title)}" onclick="openMovieModal(${movie.id})">${movie.title}</h4>
        <div class="card-meta">
          <span class="card-year">${movie.release_year || 'N/A'}</span>
          <span class="card-genre">${firstGenre}</span>
        </div>
      </div>
    </div>
  `;
}

/* ==========================================================================
   Recommendation Engine Action
   ========================================================================== */
async function recommendMovie(movieId, title) {
  const recSection = document.getElementById("recommendationSection");
  const recGrid = document.getElementById("recommendationsGrid");
  const targetTitleElem = document.getElementById("recTargetTitle");

  if (targetTitleElem) targetTitleElem.textContent = title;
  recSection.style.display = "block";
  recGrid.innerHTML = `
    <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--text-muted);">
      <div class="pulse-dot" style="margin: 0 auto 16px; width: 16px; height: 16px;"></div>
      Finding top similar films based on themes, cast & plot keywords...
    </div>
  `;

  // Smooth scroll to recommendation section
  recSection.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const res = await fetch(`/api/recommend/${movieId}?limit=10`);
    if (!res.ok) throw new Error("Could not fetch recommendations");
    const recommendations = await res.json();

    if (!recommendations || recommendations.length === 0) {
      recGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 30px; text-align: center; color: var(--text-dim);">No close recommendations found for this title.</div>`;
      return;
    }

    recGrid.innerHTML = recommendations.map(rec => createMovieCardHtml(rec, rec.match_score)).join("");
    showToast(`Generated 10 AI recommendations for "${title}"!`, "✨");
  } catch (err) {
    console.error("Error generating recommendations:", err);
    recGrid.innerHTML = `<div style="grid-column: 1 / -1; padding: 20px; color: var(--accent-rose); text-align: center;">Unable to generate recommendations right now.</div>`;
  }
}

function closeRecommendations() {
  const recSection = document.getElementById("recommendationSection");
  if (recSection) recSection.style.display = "none";
}

/* ==========================================================================
   Movie Detail Modal
   ========================================================================== */
function initModal() {
  const modal = document.getElementById("movieModal");
  const closeBtn = document.getElementById("closeModalBtn");

  if (!modal) return;

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.style.display !== "none") {
      modal.style.display = "none";
    }
  });
}

async function openMovieModal(movieId) {
  const modal = document.getElementById("movieModal");
  const modalBody = document.getElementById("modalBody");

  modalBody.innerHTML = `
    <div style="padding: 60px; text-align: center; color: var(--text-muted);">
      <div class="pulse-dot" style="margin: 0 auto 16px; width: 14px; height: 14px;"></div>
      Loading movie details...
    </div>
  `;
  modal.style.display = "flex";

  try {
    const res = await fetch(`/api/movies/${movieId}`);
    if (!res.ok) throw new Error("Could not load details");
    const m = await res.json();

    const backdropBg = m.backdrop_url || m.poster_url;
    const castChips = (m.cast || []).map(c => `<span class="cast-chip">${c}</span>`).join("") || '<span style="color: var(--text-dim);">N/A</span>';
    const genreBadges = (m.genres || []).map(g => `<span class="genre-tag">${g}</span>`).join("");

    modalBody.innerHTML = `
      <div class="modal-backdrop-header" style="background-image: url('${backdropBg}');"></div>
      <div class="modal-content-inner">
        <div class="modal-header-info">
          <img src="${m.poster_url}" alt="${escapeQuotes(m.title)}" class="modal-poster" onerror="this.src='/static/img/placeholder.svg'">
          <div class="modal-details">
            <div class="modal-badges">
              <span class="rating-pill">★ ${m.vote_average || '0.0'} TMDB</span>
              <span class="year-pill">${m.release_year || 'N/A'}</span>
              <span class="badge-featured" style="background: rgba(99, 102, 241, 0.2); color: #C7D2FE;">Popularity ${m.popularity || 0}</span>
            </div>
            <h2 class="modal-title">${m.title}</h2>
            <div class="genre-pill-group" style="margin-top: 6px;">
              ${genreBadges}
            </div>
          </div>
        </div>

        <p class="modal-overview">${m.overview || 'No synopsis available.'}</p>

        <div class="modal-grid-meta">
          <div>
            <span class="meta-label">DIRECTOR</span>
            <div class="meta-value" style="margin-top: 4px;">${m.director || 'Unknown'}</div>
          </div>
          <div>
            <span class="meta-label">TOP CAST</span>
            <div class="modal-cast-chips">
              ${castChips}
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 14px; flex-wrap: wrap;">
          <button class="btn btn-primary" onclick="recommendMovieFromModal(${m.id}, '${escapeQuotes(m.title)}')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Find Similar Movies
          </button>
          <a href="https://www.themoviedb.org/movie/${m.id}" target="_blank" class="btn btn-secondary">
            View on TMDB &nearr;
          </a>
        </div>
      </div>
    `;
  } catch (err) {
    console.error("Modal fetch error:", err);
    modalBody.innerHTML = `<div style="padding: 40px; color: var(--accent-rose); text-align: center;">Error loading movie details.</div>`;
  }
}

function recommendMovieFromModal(movieId, title) {
  document.getElementById("movieModal").style.display = "none";
  recommendMovie(movieId, title);
}

/* ==========================================================================
   Keyboard Shortcuts & Toast
   ========================================================================== */
function initKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      const input = document.getElementById("searchInput");
      if (input) {
        input.focus();
        input.select();
      }
    }
  });
}

function showToast(message, icon = "✨") {
  const toast = document.getElementById("toastNotification");
  const msgElem = document.getElementById("toastMessage");
  const iconElem = document.getElementById("toastIcon");

  if (!toast || !msgElem) return;

  msgElem.textContent = message;
  if (iconElem) iconElem.textContent = icon;

  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}

function escapeQuotes(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
