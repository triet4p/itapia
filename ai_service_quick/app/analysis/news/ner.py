import subprocess
import sys
from typing import List
import spacy
from spacy.language import Language
from transformers import pipeline

from itapia_common.schemas.entities.analysis.news import NERElement, NERReport

class TransformerNERModel:
    def __init__(self, model_name: str, ner_score_threshold: float):
        self.pipe = pipeline("ner", model=model_name, device='cpu', aggregation_strategy="average")
        self.ner_score_threshold = ner_score_threshold
        
    def recognize(self, texts: List[str]) -> List[NERReport]:
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
    """
    Lớp wrapper cho spaCy NER, với khả năng tự động tải model nếu chưa có.
    """
    def __init__(self, model_name: str):
        """
        Khởi tạo và đảm bảo model spaCy có sẵn.

        Args:
            model_name (str): Tên của model spaCy cần tải (ví dụ: "en_core_web_sm").
        """
        self.model_name = model_name
        try:
            # Cố gắng tải model như bình thường
            self.nlp: Language = spacy.load(self.model_name)
        except OSError:
            # Nếu không tìm thấy, bắt đầu quá trình tải tự động
            print(f"Spacy model '{self.model_name}' not found. Attempting to download automatically...")
            self._download_model()
            # Sau khi tải xong, thử load lại
            self.nlp: Language = spacy.load(self.model_name)
            print(f"Successfully downloaded and loaded spaCy model '{self.model_name}'.")

    def _download_model(self):
        """
        Sử dụng subprocess để chạy 'python -m spacy download ...'.
        Đây là cách làm được spaCy khuyến nghị và đáng tin cậy nhất.
        """
        # Lấy đường dẫn đến python executable đang chạy script này
        # Điều này đảm bảo chúng ta dùng đúng môi trường python/conda
        python_executable = sys.executable
        
        command = [
            python_executable, 
            "-m", "spacy", "download", 
            self.model_name
        ]
        
        try:
            # Chạy command và chờ nó hoàn thành
            # capture_output=True sẽ bắt stdout và stderr
            # text=True để output là string thay vì bytes
            # check=True sẽ ném ra CalledProcessError nếu command thất bại
            subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True
            )
        except subprocess.CalledProcessError as e:
            # Ghi log lỗi chi tiết nếu quá trình tải thất bại
            print(f"Failed to download spaCy model '{self.model_name}'.")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            # Ném lại lỗi để quá trình khởi tạo thất bại một cách rõ ràng
            raise e
        except FileNotFoundError:
            # Xử lý trường hợp không tìm thấy python executable
            print("Could not find python executable. Make sure Python is in your PATH.")
            raise

    def recognize(self, texts: List[str]) -> List[NERReport]:
        docs = self.nlp.pipe(texts)
        
        all_reports = []
        for doc in docs:
            found_entities = [
                NERElement(word=ent.text, entity_group=ent.label_) 
                for ent in doc.ents
            ]
            all_reports.append(NERReport(entities=found_entities))

        return all_reports