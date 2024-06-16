'''
Alguns dos nossos modelos serão avaliados utilizando: 
    1. Apenas o abstract como informação para o vespa. O título de um dos
        documentos servirá como query
    2. O título e o abstract como informação para o vespa. Vamos utilizar
        queries geradas por LLM.
    3. Apenas o título como informação para o vespa. O título de um dos
        documentos servirá como query. Esse caso só será avaliado com o BM25.
Para facilitar a execução dos experimentos, criamos um dicionário com os 
modelos que serão avaliados em cada caso.
'''
models = {
    'title_query': [
        "bm25_abstract_only",
        "semantic_abstract_only",
        "hybrid_abstract_only",
        "max_sim_per_context_sentence_abstract_only",
        "max_sim_cross_context_sentence_abstract_only",
        "max_sim_per_context_chunck_abstract_only",
        "max_sim_cross_context_chunck_abstract_only",
    ],
    'llm_query': {
        "bm25_title_only",
        "bm25_title_and_abstract",
        "semantic_title_and_abstract",
        "hybrid_title_and_abstract",
        "max_sim_per_context_sentence_title_and_abstract",
        "max_sim_cross_context_sentence_title_and_abstract",
        "max_sim_per_context_chunck_title_and_abstract",
        "max_sim_cross_context_chunck_title_and_abstract",
    }
}