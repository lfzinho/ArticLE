$(document).ready(function() {
    const results = [
        {
            title: 'Recent progress in the development of biomass-derived nitrogen-doped porous carbon',
            link: '#',
            snippet: 'This review offers a focused discussion on the recent progress of biomass-derived nitrogen-doped porous carbon (NPC) and its applications...',
            summary: 'This article provides a comprehensive review of the development and applications of biomass-derived nitrogen-doped porous carbon.',
            reasoning: 'Selected due to its relevance and detailed exploration of NPC synthesis methods.'
        },
        {
            title: 'Nanoarchitectured structure and surface biofunctionality of mesoporous silica nanoparticles',
            link: '#',
            snippet: 'Mesoporous silica nanoparticles (MSNs), one of the important porous materials, have garnered interest owing to their highly attractive physicochemical features and advantageous...',
            summary: 'Focuses on the unique properties and applications of mesoporous silica nanoparticles.',
            reasoning: 'Chosen for its detailed analysis of the physicochemical properties of MSNs.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
        {
            title: 'How biochar works, and when it doesn\'t: A review of mechanisms controlling soil and plant responses to biochar',
            link: '#',
            snippet: 'We synthesized 20 years of research to explain the interrelated processes that determine soil and plant responses to biochar. The properties of biochar and its effects within agricultural...',
            summary: 'Analyzes the various factors affecting the efficacy of biochar in soil and plant responses.',
            reasoning: 'Included for its extensive review of biochar mechanisms and agricultural impacts.'
        },
    ];

    function displayResults(detailType = '') {
        $('.content-section').css('margin-top', '20px');
        const resultsSection = $('#results-section');
        resultsSection.empty();
        results.forEach((result, index) => {
            let details = '';
            if (detailType && index < 3) {
                details = `<p class="${detailType}">${result[detailType]}</p>`;
            }
            const resultItem = `
                <div class="result-item">
                    <a href="${result.link}" target="_blank">${result.title}</a>
                    <p>${result.snippet}</p>
                    ${details}
                </div>
            `;
            resultsSection.append(resultItem);
        });
        resultsSection.show();
    }

    $('#show-btn').on('click', function() {
        displayResults();
    });

    $('#explain-btn').on('click', function() {
        displayResults('reasoning');
    });

    $('#summary-btn').on('click', function() {
        displayResults('summary');
    });
});
