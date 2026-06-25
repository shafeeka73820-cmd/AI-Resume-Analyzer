document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('resume', document.getElementById('resume').files[0]);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.innerText = 'Analyzing...';
    submitBtn.disabled = true;

    try {
        const response = await fetch('/analyze/', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        document.getElementById('results').classList.remove('hidden');
        document.getElementById('result-content').innerText = data.analysis || 'Analysis complete. (Note: Ensure API is returning data)';
    } catch (error) {
        alert('Error analyzing resume');
    } finally {
        submitBtn.innerText = 'Analyze My Resume';
        submitBtn.disabled = false;
    }
});
