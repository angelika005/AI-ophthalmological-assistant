# ml_service.py
import io
import cv2
import torch
import numpy as np
from PIL import Image
from transformers import AutoImageProcessor, Swinv2ForImageClassification
from typing import Dict
import logging
import os
import time

logger = logging.getLogger(__name__)

class GlaucomaDetectionService:
    def __init__(self):
        self.model_name = "pamixsun/swinv2_tiny_for_glaucoma_classification"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Загружаем модель и процессор сразу при инициализации
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = Swinv2ForImageClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model loaded and ready")

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image_rgb

    def predict(self, image_bytes: bytes) -> Dict[str, any]:
        try:
            start_time = time.perf_counter()
            image_rgb = self.preprocess_image(image_bytes)
            inputs = self.processor(image_rgb, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0]

            predicted_idx = logits.argmax(-1).item()
            predicted_label = self.model.config.id2label[predicted_idx]
            confidence = float(probabilities[predicted_idx])

            glaucoma_idx = 1 if self.model.config.id2label.get(1) == "glaucoma" else 0
            glaucoma_probability = float(probabilities[glaucoma_idx])

            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            result = {
                "predicted_label": predicted_label,
                "confidence": confidence,
                "glaucoma_probability": glaucoma_probability,
                "all_probabilities": {self.model.config.id2label[i]: float(p) for i, p in enumerate(probabilities)},
                "processing_time_ms": processing_time_ms
            }

            logger.info(f"Prediction: {predicted_label} (confidence: {confidence:.2%})")
            return result
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise

# создаем глобальный одноэкземпляр сервиса
glaucoma_service = GlaucomaDetectionService()
