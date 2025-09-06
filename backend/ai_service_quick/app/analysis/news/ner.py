"""Named Entity Recognition (NER) models for news analysis."""

import subprocess
import sys
from typing import List
import spacy
from spacy.language import Language
from transformers import pipeline

from itapia_common.schemas.entities.analysis.news import NERElement, NERReport


class TransformerNERModel:
    """Transformer-based Named Entity Recognition model."""
    
    def __init__(self, model_name: str, ner_score_threshold: float):
        """Initialize the transformer NER model.
        
        Args:
            model_name (str): Name of the transformer model to use
            ner_score_threshold (float): Minimum score threshold for entity recognition
        """
        self.pipe = pipeline("ner", model=model_name, device='cpu', aggregation_strategy="average")
        self.ner_score_threshold = ner_score_threshold
        
    def recognize(self, texts: List[str]) -> List[NERReport]:
        """Recognize named entities in texts.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[NERReport]: List of NER reports with recognized entities
        """
        entities_results = self.pipe(texts)
        reports: List[NERReport] = []
        for res in entities_results:
            elements: List[NERElement] = []
            for entity in res:
                if float(entity['score']) < self.ner_score_threshold:
                    continue
                elements.append(NERElement(
                    entity_group=entity['entity_group'],
                    word=entity['word']
                ))
            reports.append(NERReport(
                entities=elements
            ))
        return reports


class SpacyNERModel:
    """Wrapper class for spaCy NER with automatic model downloading capability."""
    
    def __init__(self, model_name: str):
        """Initialize and ensure spaCy model is available.
        
        Args:
            model_name (str): Name of the spaCy model to load (e.g., "en_core_web_sm")
        """
        self.model_name = model_name
        try:
            # Try to load model normally
            self.nlp: Language = spacy.load(self.model_name)
        except OSError:
            # If not found, start automatic download process
            print(f"Spacy model '{self.model_name}' not found. Attempting to download automatically...")
            self._download_model()
            # After downloading, try to load again
            self.nlp: Language = spacy.load(self.model_name)
            print(f"Successfully downloaded and loaded spaCy model '{self.model_name}'.")

    def _download_model(self):
        """Use subprocess to run 'python -m spacy download ...'.
        
        This is the recommended and most reliable approach by spaCy.
        """
        # Get path to python executable running this script
        # This ensures we use the correct python/conda environment
        python_executable = sys.executable
        
        command = [
            python_executable, 
            "-m", "spacy", "download", 
            self.model_name
        ]
        
        try:
            # Run command and wait for completion
            # capture_output=True captures stdout and stderr
            # text=True makes output string instead of bytes
            # check=True raises CalledProcessError if command fails
            subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True
            )
        except subprocess.CalledProcessError as e:
            # Log detailed error if download process fails
            print(f"Failed to download spaCy model '{self.model_name}'.")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            # Re-raise error to make initialization fail explicitly
            raise e
        except FileNotFoundError:
            # Handle case where python executable is not found
            print("Could not find python executable. Make sure Python is in your PATH.")
            raise

    def recognize(self, texts: List[str]) -> List[NERReport]:
        """Recognize named entities in texts using spaCy.
        
        Args:
            texts (List[str]): List of texts to analyze
            
        Returns:
            List[NERReport]: List of NER reports with recognized entities
        """
        docs = self.nlp.pipe(texts)
        
        all_reports = []
        for doc in docs:
            found_entities = [
                NERElement(word=ent.text, entity_group=ent.label_) 
                for ent in doc.ents
            ]
            all_reports.append(NERReport(entities=found_entities))

        return all_reports