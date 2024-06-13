from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..search.llm import LLM
from ..search.search_engine import SearchEngine, SearchEngineCloud, SearchEngineLocal


class QueryRequest(BaseModel):
    query: str
    response_type: str


class App:
    endpoint = "https://eb38f856.cc1e1530.z.vespa-app.cloud/"
    application = ""

    cert_path = (
        Path.home()
        / ".vespa"
        / "article.hybridsearch.default/data-plane-public-cert.pem"
    )
    key_path = (
        Path.home()
        / ".vespa"
        / "article.hybridsearch.default/data-plane-private-key.pem"
    )

    data_dir = Path.cwd() / "data"
    data_files = ["arxiv-metadata-oai-snapshot.json"]
    dataset_size_limit = 100

    def __init__(
        self,
        search_engine: SearchEngine | None = None,
        model: LLM | None = None,
        on_cloud: bool = False
    ) -> None:
        self.model = LLM() if model is None else model
        if search_engine is None:
            self.search_engine = (
                SearchEngineCloud(self.endpoint, self.cert_path, self.key_path) if on_cloud
                else SearchEngineLocal(self.data_dir, self.data_files, self.dataset_size_limit)
            )
        else:
            self.search_engine = search_engine

        self._app = FastAPI()
        self._app.add_middleware(
            CORSMiddleware,
            allow_credentials=True,
            allow_headers=["*"],
            allow_methods=["*"],
            allow_origins=["*"],
        )

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs) -> None:
        import uvicorn

        @self._app.post("/run_query")
        def run_query(request: QueryRequest):
            docs = self.search_engine.search(request.query)
            if docs.empty:
                raise HTTPException(status_code=404, detail="No documents found.")

            response = self.model.generate_response(
                request.query, docs, request.response_type
            )
            for doc in response:
                doc["link"] = "#"
            return response


        static_dir = Path(__file__).parent / "static"
        self._app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
        uvicorn.run(self._app, host=host, port=port, **kwargs)
