/**
 * Halaman Experience: semua operasi data lewat API DRF di /api/v1/experiences/
 * Konfigurasi (URL, role) dibaca dari atribut data-* pada #experience.
 * Bergantung pada utils.js (getCookie, escapeHtml) dan toast.js (showToast).
 */
(function () {
    const section = document.getElementById('experience');
    if (!section) return;

    const ZERO_ID = '00000000-0000-0000-0000-000000000000';
    const SEARCH_DEBOUNCE_DELAY = 300;
    const FORM_FIELDS = ['title', 'description', 'category', 'thumbnail', 'ended_at'];

    const config = {
        listEndpoint: section.dataset.listEndpoint,
        detailUrl: section.dataset.detailUrl,
        starUrl: section.dataset.starUrl,
        loginUrl: section.dataset.loginUrl,
        isAuthenticated: section.dataset.isAuthenticated === 'true',
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
    const editForm = document.getElementById('experience-edit-form');
    const editModal = document.getElementById('edit-experience-modal');

    let abortController;
    let searchDebounceTimer;
    let editingId = null;
    const experiencesById = new Map();

    function displayPageSection({ showLoading = false, showError = false, showEmpty = false, showGrid = false }) {
        loadingState.classList.toggle('hide', !showLoading);
        errorState.classList.toggle('hide', !showError);
        emptyState.classList.toggle('hide', !showEmpty);
        gridContainer.classList.toggle('hide', !showGrid);
    }

    function showMessage(title, message, type) {
        if (typeof showToast === 'function') showToast(title, message, type);
    }

    function endpointFor(pattern, id) {
        return pattern.replace(ZERO_ID, id);
    }

    function showGridOrEmpty() {
        const hasCards = gridContainer.children.length > 0;
        displayPageSection({ showGrid: hasCards, showEmpty: !hasCards });
    }

    function buildExperienceCardElement(experience) {
        const article = document.createElement('article');
        article.className = 'experience-card';
        article.dataset.id = experience.id;

        const thumbnailHtml = experience.thumbnail
            ? `<img src="${escapeHtml(experience.thumbnail)}" alt="Thumbnail ${escapeHtml(experience.title)}" class="experience-thumbnail">`
            : '';

        const starTitle = experience.star_count > 0
            ? `Dibintangi oleh ${escapeHtml(experience.starred_by_names)}`
            : 'Jadilah yang pertama memberi star';

        const starHtml = config.isAuthenticated
            ? `<button type="button" class="button button-star${experience.is_starred ? ' is-starred' : ''}"
                    data-action="star" title="${starTitle}">
                    <span aria-hidden="true">★</span>
                    ${experience.is_starred ? 'Unstar' : 'Star'}
                    <span class="star-count">${experience.star_count}</span>
                </button>`
            : `<a href="${escapeHtml(config.loginUrl)}" class="button" title="${starTitle}">Login untuk star (${experience.star_count})</a>`;

        const editHtml = config.canEdit
            ? '<button type="button" class="button button-secondary" data-action="edit">Edit</button>'
            : '';

        const deleteHtml = config.isSuperuser
            ? '<button type="button" class="button button-danger" data-action="delete">Hapus</button>'
            : '';

        article.innerHTML = `
            ${thumbnailHtml}
            <span class="experience-category">${escapeHtml(experience.category_display)}</span>
            <h2>${escapeHtml(experience.title)}</h2>
            <p class="experience-description">${escapeHtml(experience.description)}</p>
            <p class="experience-status">${escapeHtml(experience.status_display)}</p>
            <div class="experience-actions">${starHtml}${editHtml}${deleteHtml}</div>
        `;
        return article;
    }

    function renderExperiences(experiences) {
        experiencesById.clear();
        experiences.forEach(experience => experiencesById.set(experience.id, experience));
        gridContainer.replaceChildren(...experiences.map(buildExperienceCardElement));
        showGridOrEmpty();
    }

    function replaceCard(experience) {
        experiencesById.set(experience.id, experience);
        const current = gridContainer.querySelector(`[data-id="${CSS.escape(experience.id)}"]`);
        if (current) current.replaceWith(buildExperienceCardElement(experience));
    }

    // Ubah respons error DRF menjadi satu kalimat untuk toast.
    function apiErrorMessage(data, status) {
        const parts = [];
        Object.entries(data || {}).forEach(([field, value]) => {
            const text = [].concat(value).filter(item => typeof item === 'string').join(' ');
            if (!text) return;
            parts.push(['detail', 'non_field_errors'].includes(field) ? text : `${field}: ${text}`);
        });
        return parts.join(' ') || `Permintaan gagal (HTTP ${status}).`;
    }

    // Satu pintu untuk semua request yang mengubah data: selalu membawa X-CSRFToken.
    async function writeExperience(url, method, payload) {
        const response = await fetch(url, {
            method,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: payload === undefined ? undefined : JSON.stringify(payload),
        });
        if (response.status === 204) return null;
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(apiErrorMessage(data, response.status));
        return data;
    }

    // Field opsional yang kosong dikirim sebagai null (ended_at) / "" (thumbnail) sesuai tipe field API
    function payloadFromForm(form) {
        const fields = new FormData(form);
        const payload = {};
        FORM_FIELDS.forEach(name => {
            const value = fields.get(name);
            if (value === null) return;
            payload[name] = name === 'ended_at' && value === '' ? null : value;
        });
        return payload;
    }

    async function fetchExperiences(searchQuery = '') {
        if (abortController) abortController.abort();
        abortController = new AbortController();

        try {
            displayPageSection({ showLoading: true });

            const url = new URL(config.listEndpoint, window.location.origin);
            if (searchQuery) url.searchParams.set('title', searchQuery);

            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' },
                signal: abortController.signal,
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            renderExperiences(await response.json());
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
            await writeExperience(config.listEndpoint, 'POST', payloadFromForm(experienceForm));
            experienceForm.reset();
            document.getElementById('add-experience-modal').hidePopover();
            showMessage('Berhasil', 'Pengalaman baru berhasil ditambahkan!', 'success');
            await fetchExperiences(searchInput.value.trim());
        } catch (error) {
            showMessage('Gagal menambahkan pengalaman', error.message, 'error');
        } finally {
            submitButton.disabled = false;
        }
    }

    function openEditModal(id) {
        const experience = experiencesById.get(id);
        if (!experience || !editForm) return;
        editingId = id;
        editForm.elements.title.value = experience.title;
        editForm.elements.description.value = experience.description;
        editForm.elements.category.value = experience.category;
        editForm.elements.thumbnail.value = experience.thumbnail || '';
        editForm.elements.ended_at.value = experience.ended_at ? experience.ended_at.slice(0, 10) : '';
        editModal.showPopover();
    }

    async function saveEdit(event) {
        event.preventDefault();
        if (!editingId) return;
        const submitButton = editForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;

        try {
            const updated = await writeExperience(
                endpointFor(config.detailUrl, editingId), 'PATCH', payloadFromForm(editForm),
            );
            editModal.hidePopover();
            replaceCard(updated);
            showMessage('Berhasil', 'Pengalaman berhasil diperbarui!', 'success');
        } catch (error) {
            showMessage('Gagal memperbarui pengalaman', error.message, 'error');
        } finally {
            submitButton.disabled = false;
        }
    }

    // Star / edit / hapus lewat event delegation satu listener untuk semua kartu
    gridContainer.addEventListener('click', async function (event) {
        const button = event.target.closest('button[data-action]');
        const card = event.target.closest('.experience-card');
        if (!button || !card || button.disabled) return;

        const id = card.dataset.id;
        const action = button.dataset.action;

        if (action === 'edit') {
            openEditModal(id);
            return;
        }
        if (action === 'delete' && !window.confirm('Yakin ingin menghapus experience ini?')) return;

        button.disabled = true;
        try {
            if (action === 'star') {
                replaceCard(await writeExperience(endpointFor(config.starUrl, id), 'POST'));
                return;
            }
            await writeExperience(endpointFor(config.detailUrl, id), 'DELETE');
            experiencesById.delete(id);
            card.remove();
            showGridOrEmpty();
            showMessage('Berhasil', 'Pengalaman berhasil dihapus.', 'success');
        } catch (error) {
            button.disabled = false;
            showMessage('Gagal', error.message, 'error');
        }
    });

    searchInput.addEventListener('input', function () {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => fetchExperiences(searchInput.value.trim()), SEARCH_DEBOUNCE_DELAY);
    });

    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();
        clearTimeout(searchDebounceTimer);
        fetchExperiences(searchInput.value.trim());
    });

    if (experienceForm) experienceForm.addEventListener('submit', addExperience);
    if (editForm) editForm.addEventListener('submit', saveEdit);

    fetchExperiences(searchInput.value.trim());
})();
