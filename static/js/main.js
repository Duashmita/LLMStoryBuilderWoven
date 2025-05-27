document.addEventListener('DOMContentLoaded', function() {
    // Handle pronouns selection
    const pronounsSelect = document.getElementById('pronouns');
    const otherPronounsDiv = document.getElementById('otherPronouns');
    
    if (pronounsSelect) {
        pronounsSelect.addEventListener('change', function() {
            if (this.value === 'other') {
                otherPronounsDiv.classList.remove('hidden');
            } else {
                otherPronounsDiv.classList.add('hidden');
            }
        });
    }

    // Handle form submission
    const storyForm = document.getElementById('storyForm');
    if (storyForm) {
        storyForm.addEventListener('submit', function(e) {
            // Validate form
            const requiredFields = storyForm.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    // Add error message
                    let errorMsg = field.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.classList.add('error-message');
                        field.parentNode.insertBefore(errorMsg, field.nextSibling);
                    }
                    errorMsg.textContent = 'This field is required';
                } else {
                    field.classList.remove('error');
                    // Remove error message if exists
                    const errorMsg = field.nextElementSibling;
                    if (errorMsg && errorMsg.classList.contains('error-message')) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // Handle response form submission
    const responseForm = document.getElementById('responseForm');
    if (responseForm) {
        responseForm.addEventListener('submit', function(e) {
            const responseInput = this.querySelector('input[name="user_response"]');
            if (!responseInput.value.trim()) {
                e.preventDefault();
                responseInput.classList.add('error');
                // Add error message
                let errorMsg = responseInput.nextElementSibling;
                if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                    errorMsg = document.createElement('div');
                    errorMsg.classList.add('error-message');
                    responseInput.parentNode.insertBefore(errorMsg, responseInput.nextSibling);
                }
                errorMsg.textContent = 'Please enter your response';
            } else {
                responseInput.classList.remove('error');
                // Remove error message if exists
                const errorMsg = responseInput.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error-message')) {
                    errorMsg.remove();
                }
            }
        });
    }

    // Add smooth scrolling for story paragraphs and user response
    const storyContent = document.querySelector('.story-content');
    if (storyContent) {
        const lastElement = storyContent.lastElementChild;
        if (lastElement) {
            lastElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }

    // Add animation to personality score bars
    const scoreBars = document.querySelectorAll('.score-fill');
    scoreBars.forEach(bar => {
        const score = parseInt(bar.dataset.score);
        const width = ((score + 5) / 10) * 100;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = `${width}%`;
        }, 100);
    });
}); 