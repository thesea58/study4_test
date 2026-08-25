// STUDY4 TOEIC Results Scraper
// Copy and paste this code into your Browser Console (F12 -> Console) on your STUDY4 results page:
// https://study4.com/tests/6855/toeic-lr-collection-1-test-4/results/37894524/#result-answers

(async () => {
    console.log("Starting scraping process...");
    
    // Find all question links
    const questionLinks = Array.from(document.querySelectorAll('a.result-question-item'));
    console.log(`Found ${questionLinks.length} questions to scrape.`);
    
    if (questionLinks.length === 0) {
        console.error("No question items found! Make sure you are on the result page.");
        return;
    }
    
    const results = [];
    const batchSize = 5; // Fetch 5 questions concurrently to avoid overload
    
    for (let i = 0; i < questionLinks.length; i += batchSize) {
        const batch = questionLinks.slice(i, i + batchSize);
        console.log(`Processing batch ${Math.floor(i / batchSize) + 1} of ${Math.ceil(questionLinks.length / batchSize)}...`);
        
        const batchPromises = batch.map(async (link) => {
            const number = link.innerText.strip ? link.innerText.strip() : link.innerText.trim();
            const href = link.getAttribute('data-href');
            
            let status = 'unanswered';
            if (link.classList.contains('correct')) status = 'correct';
            else if (link.classList.contains('wrong')) status = 'wrong';
            
            if (!href) {
                console.warn(`Question ${number} has no data-href`);
                return null;
            }
            
            const fullUrl = window.location.origin + href;
            try {
                const res = await fetch(fullUrl);
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                const htmlText = await res.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlText, 'text/html');
                
                // Extract QID
                const qWrapper = doc.querySelector('.question-wrapper');
                const qid = qWrapper ? qWrapper.getAttribute('data-qid') : '';
                
                // Extract Question Text
                const qTextEl = doc.querySelector('.question-text');
                const questionText = qTextEl ? qTextEl.innerHTML.trim() : '';
                
                // Extract Context/Passage/Audio
                const contextEl = doc.querySelector('.result-question-context');
                const context = contextEl ? contextEl.innerHTML.trim() : '';
                
                // Extract Part/Concepts
                const conceptTags = Array.from(doc.querySelectorAll('.result-question-concepts .tag'));
                const tags = conceptTags.map(t => t.innerText.trim());
                let part = '';
                for (const tag of tags) {
                    if (tag.toLowerCase().includes('part')) {
                        part = tag;
                        break;
                    }
                }
                
                // Extract Choices
                const choiceEls = Array.from(doc.querySelectorAll('.question-answers .form-check'));
                const choices = choiceEls.map(el => {
                    const input = el.querySelector('input');
                    const label = el.querySelector('label');
                    return {
                        value: input ? input.value : '',
                        checked: input ? input.checked : false,
                        is_user_wrong: input ? input.classList.contains('wrong') : false,
                        label: label ? label.innerHTML.trim() : ''
                    };
                });
                
                // Extract Correct Answer
                const correctEl = doc.querySelector('.text-success');
                let correctAnswer = '';
                if (correctEl) {
                    const match = correctEl.innerText.match(/Đáp án đúng:\s*([A-D])/);
                    if (match) correctAnswer = match[1];
                    else correctAnswer = correctEl.innerText.replace('Đáp án đúng:', '').trim();
                }
                
                // Extract Explanation
                const expEl = doc.querySelector('.question-explanation-wrapper .collapse');
                const explanation = expEl ? expEl.innerHTML.trim() : '';
                
                return {
                    number,
                    qid,
                    status,
                    part,
                    tags,
                    questionText,
                    context,
                    choices,
                    correctAnswer,
                    explanation,
                    embedUrl: fullUrl
                };
            } catch (err) {
                console.error(`Failed to fetch question ${number}:`, err);
                return {
                    number,
                    status,
                    embedUrl: fullUrl,
                    error: err.message
                };
            }
        });
        
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults.filter(r => r !== null));
        
        // Short delay between batches
        await new Promise(r => setTimeout(r, 200));
    }
    
    console.log("Scraping completed! Saving results...");
    
    // Save to file
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href",     dataStr     );
    downloadAnchor.setAttribute("download", "study4_scraped_results.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    
    console.log("Download triggered! Please move the downloaded file 'study4_scraped_results.json' to your workspace directory d:\\4.TOEIC\\study4");
})();
