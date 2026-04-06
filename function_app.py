import azure.functions as func
import logging
import csv
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Iterable, Tuple

from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

MODEL_ID = "prebuilt-layout"

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="idocumentshttp")
def idocumentshttp(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        
        def load_settings():
            load_dotenv()
            settings = {
                "endpoint": os.getenv("AZURE_DOCUMENTINTELLIGENCE_ENDPOINT"),
                "key": os.getenv("AZURE_DOCUMENTINTELLIGENCE_KEY"),
                "api_version": os.getenv("AZURE_DOCUMENTINTELLIGENCE_API_VERSION") or None
            }
            if not settings.endpoint or not settings.key:
                raise SystemExit("Azure Document Intelligence endpoint and key must be set in environment variables.")
            return settings.endpoint, settings.key, settings.api_version
        
        def get_client(endpoint: str, key: str, api_version: str) -> DocumentIntelligenceClient:

            return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key), api_version=api_version)
            
        def analyze_file(client: DocumentIntelligenceClient, file_path: str) -> Dict[str, Any]:
            with open(file_path, "rb") as f:
                document = f.read()
            poller = client.begin_analyze_document(MODEL_ID,body=AnalyzeDocumentRequest(bytes_source=f.read()))
            result = poller.result()
            return result
        
        def extract_tables(result: Dict[str, Any]) -> List[Dict[str, Any]]:
            tables_out = List[Dict[str, Any]] = []
            for idx, table in enumerate(result.tables or []):
                rows = table.row_count
                columns = table.column_count
                #initialize matrix
                matrix: List[List[str]] = [["" for _ in range(columns)] for _ in range(rows)]
                for cell in table.cells:
                    r = cell.row_index
                    c = cell.column_index
                    text = cell.content if hasattr(cell, "content") else ""
                    #handle Spans
                    row_span = getattr(cell, "row_span", 1) or 1
                    column_span = getattr(cell, "column_span", 1) or 1
                    for r in range(r, r + row_span):
                        for j in range(c, c + column_span):
                            matrix[i][j] = text
                    tables_out.append({
                        "table_index": idx,
                        "row_count": rows,
                        "column_count": columns,
                        "cells": matrix
                    })
                   
            return tables_out
        
        #return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )