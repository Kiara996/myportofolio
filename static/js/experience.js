/**
 * Halaman Experience: render kartu lewat AJAX, search, dan tambah via modal.
 * Konfigurasi (URL, role) dibaca dari atribut data-* pada #experience.
 * Bergantung pada utils.js (getCookie, escapeHtml) dan toast.js (showToast).
 */
(function () {
    const section = document.getElementById('experience');
    if (!section) return;

    const ZERO_ID = '00000000-0000-0000-0000-000000000000';
    const SEARCH_DEBOUNCE_DELAY = 300;

    const config = {
        listEndpoint: section.dataset.listEndpoint,
        createEndpoint: section.dataset.createEndpoint,
        starUrl: section.dataset.starUrl,
        editUrl: section.dataset.editUrl,
        deleteUrl: section.dataset.deleteUrl,
        isSuperuser: section.dataset.isSuperuser === 'true',
        canEdit: section.dataset.canEdit === 'true',
    };

    const loadingState = document.getElementById('loading');
    const errorState = document.getElementById('error');
    const emptyState = document.getElementById('empty');
    const gridContainer = document.getElementById('grid');
    const searchForm = document.getElementById('experience-search-form');
    const searchInput = document.getElementById('search-input');
    const experienceForm = document.getElementById('experience-form');

    let abortController;
    let searchDebounceTimer;

    function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
        loadingState.classList.toggle('hide', !showLoading);
        errorState.classList.toggle('hide', !showError);
        emptyState.classList.toggle('hide', !showEmpty);
        gridContainer.classList.toggle('hide', !showGrid);
    }

    function csrfInputHtml() {
        return `<input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(getCookie('csrftoken'))}">`;
    }

    function showMessage(title, message, type) {
        if (typeof showToast === 'function') showToast(title, message, type);
    }

    // Semua teks dari server di-escape untuk mencegah XSS
    function buildExperienceCardElement(item) {
        const experience = item.fields;
        const id = item.pk;

        const article = document.createElement('article');
        article.className = 'experience-card';

        const thumbnailHtml = experience.thumbnail
            ? `<img src="${escapeHtml(experience.thumbnail)}" alt="Thumbnail ${escapeHtml(experience.title)}" class="experience-thumbnail">`
            : '';

        const starUrl = config.starUrl.replace(ZERO_ID, id);
        const editUrl = config.editUrl.replace(ZERO_ID, id);
        const deleteUrl = config.deleteUrl.replace(ZERO_ID, id);

        const editHtml = config.canEdit
            ? `<a href="${editUrl}" class="button button-secondary">Edit</a>`
            : '';

        const deleteHtml = config.isSuperuser
            ? `<form method="post" action="${deleteUrl}" style="display:inline;">
                    ${csrfInputHtml()}
                    <button type="submit" class="button button-danger" onclick="return confirm('Yakin ingin menghapus experience ini?');">Hapus</button>
                </form>`
            : '';

        const starredClass = experience.is_starred ? ' is-starred' : '';
        const starText = experience.is_starred ? 'Unstar' : 'Star';
        const starTitle = experience.star_count > 0
            ? `Dibintangi oleh ${escapeHtml(experience.starred_by_names)}`
            : 'Jadilah yang pertama memberi star';

        article.innerHTML = `
            ${thumbnailHtml}
            <span class="experience-category">${escapeHtml(experience.category_display)}</span>
            <h2>${escapeHtml(experience.title)}</h2>
            <p class="experience-description">${escapeHtml(experience.description)}</p>
            <p class="experience-status">${escapeHtml(experience.status_display)}</p>
            <div class="experience-actions">
                <form method="post" action="${starUrl}" class="star-form">
                    ${csrfInputHtml()}
                    <button type="submit" class="button button-star${starredClass}" title="${starTitle}">
                        <span aria-hidden="true">★</span>
                        ${starText}
                        <span class="star-count">${experience.star_count}</span>
                    </button>
                </form>
                ${editHtml}
                ${deleteHtml}
            </div>
        `;
        return article;
    }

    function closeExperienceModal() {
        const modal = document.getElementById('add-experience-modal');
        if (modal) modal.hidePopover();
    }

    async function fetchExperiences(searchQuery = '') {
        if (abortController) abortController.abort();
        abortController = new AbortController();

        try {
            displayPageSection({ showLoading: true });

            const url = searchQuery
                ? `${config.listEndpoint}?title=${encodeURIComponent(searchQuery)}`
                : config.listEndpoint;

            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' },
                signal: abortController.signal,
            });
            if (!response.ok) throw new Error('Failed to fetch data');

            const data = await response.json();

            if (data.length === 0) {
                displayPageSection({ showEmpty: true });
                return;
            }

            gridContainer.innerHTML = '';
            data.forEach(item => gridContainer.appendChild(buildExperienceCardElement(item)));
            displayPageSection({ showGrid: true });
        } catch (error) {
            if (error.name === 'AbortError') return;
            console.error('Error loading experiences:', error);
            displayPageSection({ showError: true });
        }
    }

    async function addExperience(event) {
        event.preventDefault();

        const submitButton = experienceForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const response = await fetch(config.createEndpoint, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                body: new FormData(experienceForm),
            });
            const result = await response.json().catch(() => ({}));

            if (response.ok) {
                experienceForm.reset();
                closeExperienceModal();
                showMessage('Berhasil', 'Pengalaman baru berhasil ditambahkan!', 'success');
                fetchExperiences(searchInput.value.trim());
                return;
            }

            let errorMsg = 'Gagal menambahkan pengalaman.';
            if (result.errors) {
                errorMsg = Object.values(result.errors).flat().map(e => e.message).join(' ');
            } else if (result.message) {
                errorMsg = result.message;
            }
            showMessage('Gagal', errorMsg, 'error');
        } catch (error) {
            console.error('Error adding experience:', error);
            showMessage('Error', 'Tidak dapat terhubung ke server.', 'error');
        } finally {
            submitButton.disabled = false;
        }
    }

    searchInput.addEventListener('input', function () {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => fetchExperiences(searchInput.value.trim()), SEARCH_DEBOUNCE_DELAY);
    });

    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();
        clearTimeout(searchDebounceTimer);
        fetchExperiences(searchInput.value.trim());
    });

    if (experienceForm) {
        experienceForm.addEventListener('submit', addExperience);
    }

    fetchExperiences(searchInput.value.trim());
})();