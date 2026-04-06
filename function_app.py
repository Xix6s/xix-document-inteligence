import azure.functions as func
import logging
import csv
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any, Iterable, Tuple
import json

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table as RichTable
from rich import box

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
            poller = client.begin_analyze_document(MODEL_ID, body=AnalyzeDocumentRequest(bytes_source=document))
            result = poller.result()
            return result
        
        def extract_tables(result: Dict[str, Any]) -> List[Dict[str, Any]]:
            tables_out: List[Dict[str, Any]] = []
            for idx, table in enumerate(result.tables or []):
                rows = table.row_count
                columns = table.column_count
                #initialize matrix
                matrix: List[List[str]] = [["" for _ in range(columns)] for _ in range(rows)]
                for cell in table.cells:
                    row_index = cell.row_index
                    column_index = cell.column_index
                    text = cell.content if hasattr(cell, "content") else ""
                    #handle Spans
                    row_span = getattr(cell, "row_span", 1) or 1
                    column_span = getattr(cell, "column_span", 1) or 1
                    for r in range(row_index, row_index + row_span):
                        for c in range(column_index, column_index + column_span):
                            matrix[r][c] = text
                tables_out.append({
                    "table_index": idx,
                    "row_count": rows,
                    "column_count": columns,
                    "cells": matrix
                })
            return tables_out
        
        def save_as_csv(tables: List[Dict[str, Any]], output_dir: Path, stem: str):
            for t in tables:
                filename = output_dir / f"{stem}_table.csv"
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for row in t["cells"]:
                        writer.writerow(row)
        def save_as_json(tables: List[Dict[str, Any]], output_dir: Path, stem: str):
            filename = output_dir / f"{stem}_table.json"
            with open(filename, "w", encoding="utf-8") as f:
                    json.dump(tables, f, ensure_ascii=False, indent=4)
                    
                    
        def pretty_print_tables(tables: List[Dict[str, Any]]):
            for t in tables:
                table = RichTable(title=f"Table {t['table_index']}", box=box.SIMPLE) #fix
                #add columns
                for c in range(t["column_count"]):
                    table.add_column(f"Column {c}")
                #add rows
                for r in range(t["row_count"]):
                    row_data = t["cells"][r]
                    table.add_row(*row_data)

                

        
        #return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.", status_code=200)
