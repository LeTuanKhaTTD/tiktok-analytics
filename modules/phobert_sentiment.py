# -*- coding: utf-8 -*-
"""
modules/phobert_sentiment.py
────────────────────────────
Tích hợp model PhoBERT đã fine-tune vào Streamlit dashboard.

Cách dùng:
    from modules.phobert_sentiment import PhoBERTSentiment
    analyzer = PhoBERTSentiment()                           # tự tìm model
    result   = analyzer.predict("k thích ktx lắm")
    # → {'sentiment': 'negative', 'confidence': 0.87, 'scores': {...}}

Đặt model vào: tiktok_analytics/models/phobert_tvu_sentiment/
"""

import os
import json
import re
import unicodedata
from pathlib import Path

try:
    from .text_preprocessor import preprocess as shared_preprocess
except ImportError:
    shared_preprocess = None

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# ── Teen-code dictionary (đồng bộ với phobert_finetune.ipynb) ─────────────────
TEENCODE = {
    'k': 'không', 'ko': 'không', 'kh': 'không', 'khong': 'không',
    'đc': 'được', 'dc': 'được', 'đk': 'được',
    'mn': 'mọi người', 'mng': 'mọi người', 'mk': 'mình',
    'sv': 'sinh viên', 'hs': 'học sinh', 'gv': 'giáo viên',
    'tvu': 'trường đại học trà vinh', 'ktx': 'ký túc xá', 'hp': 'học phí',
    'nt': 'nhắn tin', 'ib': 'nhắn tin', 'pm': 'nhắn tin',
    'cx': 'cũng', 'cg': 'cũng', 'ntn': 'như thế nào',
    'tks': 'cảm ơn', 'thks': 'cảm ơn', 'ty': 'cảm ơn',
    'ok': 'ổn', 'oke': 'ổn', 'okey': 'ổn',
    'ad': 'admin', 'r': 'rồi', 'rùi': 'rồi',
    'j': 'gì', 'z': 'vậy', 'v': 'vậy', 'vs': 'với',
    'g': 'gì', 'tg': 'thời gian', 'h': 'giờ',
    'ms': 'mới', 'ns': 'nói', 'ngta': 'người ta',
    'tui': 'tôi', 'mik': 'mình', 'bn': 'bạn',
    'bh': 'bao giờ', 'dag': 'đang', 'đag': 'đang',
}

EMOJI_MAP = {
    '😭': ' rất buồn ', '😢': ' buồn ', '😔': ' buồn ',
    '😡': ' tức giận ', '😤': ' bực bội ', '👎': ' không tốt ',
    '😍': ' rất thích ', '❤️': ' yêu thích ', '🥰': ' yêu quý ',
    '😊': ' vui ', '😄': ' rất vui ', '🤩': ' tuyệt vời ',
    '🔥': ' tuyệt ', '👏': ' khen ngợi ', '🎉': ' chúc mừng ',
    '👍': ' tốt ', '✅': ' đồng ý ', '💪': ' cố lên ',
    '🙏': ' cảm ơn ', '💯': ' hoàn hảo ',
    '😂': ' hài hước ', '🤣': ' buồn cười ', '😅': ' ngại ',
}

ID2LABEL = {0: 'positive', 1: 'neutral', 2: 'negative'}

# ── Default model path ────────────────────────────────────────────────────────
_DEFAULT_PATHS = [
    Path(__file__).parent.parent / 'models' / 'phobert_tvu_sentiment',
    Path(__file__).parent.parent / 'models',
    Path('models') / 'phobert_tvu_sentiment',
    Path('models'),
    Path('phobert_tvu_sentiment'),
]


def _is_model_dir(path: Path) -> bool:
    """Check if a path contains a loadable Hugging Face model."""
    return (path / 'config.json').exists() and (path / 'tokenizer_config.json').exists()


def _preprocess(text: str) -> str:
    """Tiền xử lý text trước khi đưa vào PhoBERT."""
    if shared_preprocess is not None:
        return shared_preprocess(text, normalize_teen=True, normalize_emojis=True)

    if not isinstance(text, str) or not text.strip():
        return ''
    text = unicodedata.normalize('NFC', text)
    for emoji, rep in EMOJI_MAP.items():
        text = text.replace(emoji, rep)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    text = text.lower()
    tokens = text.split()
    tokens = [TEENCODE.get(t, t) for t in tokens]
    text = ' '.join(tokens)
    text = re.sub(
        r'[^\w\sàáâãèéêìíòóôõùúýăđơưạảấầẩẫậắặẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵ'
        r'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]', ' ', text
    )
    return re.sub(r'\s+', ' ', text).strip()


class PhoBERTSentiment:
    """
    Wrapper nhẹ cho PhoBERT fine-tuned trên comment TVU.

    Parameters
    ----------
    model_path : str | Path | None
        Đường dẫn đến thư mục model.  Nếu None, tự tìm ở các path mặc định.
    max_len : int
        Độ dài tối đa của chuỗi token (phải khớp với lúc train, mặc định 128).
    """

    def __init__(self, model_path=None, max_len: int = 128):
        if not _TORCH_AVAILABLE:
            raise ImportError(
                "Cần cài: pip install torch transformers\n"
                "Hoặc: pip install torch transformers --index-url https://download.pytorch.org/whl/cpu"
            )

        # Tìm model path
        if model_path is None:
            for p in _DEFAULT_PATHS:
                if _is_model_dir(p):
                    model_path = p
                    break
            if model_path is None:
                raise FileNotFoundError(
                    "Không tìm thấy model PhoBERT.\n"
                    "Hãy giải nén phobert_tvu_sentiment.zip vào MỘT trong các vị trí:\n"
                    "  tiktok_analytics/models/phobert_tvu_sentiment/\n"
                    "  tiktok_analytics/models/\n"
                    "Xem hướng dẫn trong phobert_finetune.ipynb"
                )

        model_path = Path(model_path)
        self.model_path = str(model_path)
        self.max_len    = max_len
        self.device     = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self.model     = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        self.model     = self.model.to(self.device)
        self.model.eval()

        # Đọc metadata nếu có
        meta_file = model_path / 'training_metadata.json'
        self.metadata = {}
        if meta_file.exists():
            with open(meta_file, encoding='utf-8') as f:
                self.metadata = json.load(f)

    # ── Single prediction ─────────────────────────────────────────────────────

    def predict(self, text: str) -> dict:
        """
        Dự đoán sentiment cho một comment.

        Returns
        -------
        dict với các key:
            sentiment   : 'positive' | 'neutral' | 'negative'
            confidence  : float [0, 1]
            scores      : {'positive': float, 'neutral': float, 'negative': float}
            text_clean  : str  (text sau tiền xử lý)
        """
        clean = _preprocess(text)
        if not clean:
            return {
                'sentiment': 'neutral', 'confidence': 0.5,
                'scores': {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
                'text_clean': ''
            }

        enc = self.tokenizer(
            clean,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        with torch.no_grad():
            logits = self.model(
                input_ids=enc['input_ids'].to(self.device),
                attention_mask=enc['attention_mask'].to(self.device)
            ).logits

        import torch.nn.functional as F
        probs = F.softmax(logits, dim=1).cpu().numpy()[0]
        pred_idx = int(probs.argmax())

        return {
            'sentiment':  ID2LABEL[pred_idx],
            'confidence': float(probs[pred_idx]),
            'scores': {
                'positive': float(probs[0]),
                'neutral':  float(probs[1]),
                'negative': float(probs[2]),
            },
            'text_clean': clean,
        }

    # ── Batch prediction ──────────────────────────────────────────────────────

    def predict_batch(self, texts: list, batch_size: int = 32, progress_callback=None) -> list:
        """
        Dự đoán cho danh sách comment.

        Parameters
        ----------
        texts : list[str]
        batch_size : int
        progress_callback : callable(done, total) | None   # dùng cho Streamlit progress bar

        Returns
        -------
        list[dict] — mỗi item có cùng format với predict()
        """
        results = []
        total = len(texts)
        for i in range(0, total, batch_size):
            batch_texts = texts[i:i + batch_size]
            cleans = [_preprocess(t) for t in batch_texts]

            enc = self.tokenizer(
                cleans,
                add_special_tokens=True,
                max_length=self.max_len,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )

            with torch.no_grad():
                logits = self.model(
                    input_ids=enc['input_ids'].to(self.device),
                    attention_mask=enc['attention_mask'].to(self.device)
                ).logits

            import torch.nn.functional as F
            probs_batch = F.softmax(logits, dim=1).cpu().numpy()

            for j, probs in enumerate(probs_batch):
                pred_idx = int(probs.argmax())
                results.append({
                    'sentiment':  ID2LABEL[pred_idx],
                    'confidence': float(probs[pred_idx]),
                    'scores': {
                        'positive': float(probs[0]),
                        'neutral':  float(probs[1]),
                        'negative': float(probs[2]),
                    },
                    'text_clean': cleans[j],
                })

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

        return results

    # ── Info ──────────────────────────────────────────────────────────────────

    def info(self) -> dict:
        """Trả về thông tin model."""
        return {
            'model_path':     self.model_path,
            'device':         str(self.device),
            'max_len':        self.max_len,
            'fine_tuned_on':  self.metadata.get('fine_tuned_on'),
            'train_sources':  self.metadata.get('train_sources'),
            'test_accuracy':  self.metadata.get('test_accuracy'),
            'test_f1':        self.metadata.get('test_f1_macro') or self.metadata.get('test_f1'),
            'best_val_f1':    self.metadata.get('best_val_macro_f1') or self.metadata.get('best_val_f1'),
            'train_size':     self.metadata.get('train_size'),
            'val_size':       self.metadata.get('val_size'),
            'test_size':      self.metadata.get('test_size'),
            'epochs':         self.metadata.get('epochs'),
        }


# ── Module-level check ────────────────────────────────────────────────────────

def is_model_available() -> bool:
    """Kiểm tra xem model đã được cài đặt chưa."""
    if not _TORCH_AVAILABLE:
        return False
    for p in _DEFAULT_PATHS:
        if _is_model_dir(p):
            return True
    return False


def get_model_path() -> str | None:
    """Trả về đường dẫn đến model nếu có."""
    for p in _DEFAULT_PATHS:
        if _is_model_dir(p):
            return str(p)
    return None
