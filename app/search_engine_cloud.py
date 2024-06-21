import pandas as pd
from vespa.io import VespaQueryResponse
from vespa.application import Vespa

class SearchEngine:
    def __init__(self, endpoint, cert_path, key_path):
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.app = Vespa(self.endpoint, cert=self.cert_path, key=self.key_path)

    def hits_to_df(self, response:VespaQueryResponse) -> pd.DataFrame:
        records = []
        fields = ["id", "title", "body"]
        for hit in response.hits:
            record = {}
            for field in fields:
                record[field] = hit['fields'][field]
            record["relevance"] = hit["relevance"]
            records.append(record)
        return pd.DataFrame(records)

    def search(self, query, n_hits: int = 5):
        with self.app.syncio(connections=1) as session:
            response:VespaQueryResponse = session.query(
                yql=f"select * from sources * where userQuery() limit {n_hits}",
                query=query,
                ranking="fusion",
            )
        assert(response.is_successful())
        return self.hits_to_df(response)
