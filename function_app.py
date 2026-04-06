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
                "key": os.getenv("AZURE_DOCUMENTINTELLIGENCE_KEY")
            }
            if not settings.endpoint or not settings.key:
                raise SystemExit("Azure Document Intelligence endpoint and key must be set in environment variables.")
            return settings.endpoint, settings.key
        
        
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )