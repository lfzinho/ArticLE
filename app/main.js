$(document).ready(function() {
    function fetchResults(query, responseType) {
        return $.ajax({
            url: 'http://127.0.0.1:8000/run_query',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ query: query, response_type: responseType }),
            success: function(data) {
                console.log("Success:", data);
            },
            error: function(xhr, status, error) {
                console.error("Error:", status, error);
            }
        });
    }

    function displayResults(results, detailType = '') {
        console.log(displayResults)
        $('.content-section').css('margin-top', '20px');
        const resultsSection = $('#results-section');
        resultsSection.empty();
        results.forEach((result, index) => {
            let details = '';
            if (detailType && result[detailType] && index < 3) {
                details = `<p class="${detailType}">${result[detailType]}</p>`;
            }
            const relevance = result.relevance !== undefined ? result.relevance.toFixed(2) : 'N/A';
            const resultItem = `
                <div class="result-item">
                    <a href="${result.link || '#'}" target="_blank">${result.title || 'No title available'}</a>
                    <p>${result.body || 'No snippet available'}</p>
                    ${details}
                    <p><strong>Relevance:</strong> ${relevance}</p>
                </div>
            `;
            resultsSection.append(resultItem);
        });
        resultsSection.show();
    }

    function markButtonSelected(buttonId) {
        $('.search-btn').removeClass('selected');
        $(`#${buttonId}`).addClass('selected');
    }

    $('#show-btn').on('click', function() {
        const query = $('#search-input').val();
        fetchResults(query, 'Just Show the Results')
            .done(function(results) {
                displayResults(results);
                markButtonSelected('show-btn');
            })
            .fail(function() {
                console.error('Error fetching results');
            });
    });

    $('#explain-btn').on('click', function() {
        const query = $('#search-input').val();
        fetchResults(query, 'Explain the Reasoning')
            .done(function(results) {
                displayResults(results, 'reasoning');
                markButtonSelected('explain-btn');
            })
            .fail(function() {
                console.error('Error fetching results');
            });
    });

    $('#summary-btn').on('click', function() {
        const query = $('#search-input').val();
        fetchResults(query, 'Informative Summary')
            .done(function(results) {
                displayResults(results, 'summary');
                markButtonSelected('summary-btn');
            })
            .fail(function() {
                console.error('Error fetching results');
            });
    });
});
