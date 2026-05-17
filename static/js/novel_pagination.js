document.addEventListener('DOMContentLoaded', () => {
    // 1. Get DOM elements and core data
    const listUl = document.getElementById('chapter-list-ul');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfoSpan = document.getElementById('current-page-info');
    const wrapper = document.getElementById('chapter-list-wrapper');
    
    const novelId = '{{ novel_id }}'; 
    let currentPage = 1;

    async function loadChapters(page) {
        if (page < 1) return;

        wrapper.innerHTML = '<p style="text-align: center; padding: 50px;">Loading chapters...</p>';

        const apiUrl = `/api/novel/${novelId}/chapters?page=${page}`;
        
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            
            currentPage = data.page;

            let chapterHtml = '';
            if (data.items.length > 0) {
                data.items.forEach(chapter => {
                    chapterHtml += `
                        <li>
                            <a href="${chapter.url}">
                                <span class="chapter-number-full">Chapter ${chapter.number}:</span> 
                                ${chapter.title}
                                <span class="chapter-length">${chapter.length}</span>
                            </a>
                        </li>
                    `;
                });
                
                // Update the wrapper with the new list structure
                wrapper.innerHTML = `<ul class="chapter-list full-list" id="chapter-list-ul">${chapterHtml}</ul>`;
            } else {
                wrapper.innerHTML = '<p style="text-align: center; padding: 50px;">No more chapters found.</p>';
            }


            // 3. Update pagination controls
            pageInfoSpan.textContent = `Page ${data.page} of ${data.total_pages}`;

            // Handle Previous Button
            if (data.has_prev) {
                prevBtn.classList.remove('disabled');
                prevBtn.onclick = () => loadChapters(data.page - 1);
            } else {
                prevBtn.classList.add('disabled');
                prevBtn.onclick = null;
            }

            // Handle Next Button
            if (data.has_next) {
                nextBtn.classList.remove('disabled');
                nextBtn.onclick = () => loadChapters(data.page + 1);
            } else {
                nextBtn.classList.add('disabled');
                nextBtn.onclick = null;
            }
            
            // Scroll to the top of the chapter list wrapper
            wrapper.scrollTo({ top: 0, behavior: 'smooth' });

        } catch (error) {
            console.error('Error fetching chapters:', error);
            wrapper.innerHTML = '<p style="text-align: center; color: red; padding: 50px;">Could not load chapters.</p>';
        }
    }

    loadChapters(currentPage);
});