"""Text Preprocessor - Tiền xử lý bình luận TikTok tiếng Việt

Xử lý các vấn đề đặc thù của dữ liệu TikTok:
- Làm sạch sơ bộ cho bước gán nhãn thủ công
- Chuẩn hóa teen-code / viết tắt tiếng Việt
- Chuyển emoji thành text mô tả cảm xúc
- Phát hiện và loại bỏ duplicate
- Lọc comment không có giá trị phân tích
"""
import html
import re
import unicodedata
from hashlib import md5
from typing import Optional


# ============================================================================
# TỪ ĐIỂN TEEN-CODE TIẾNG VIỆT
# ============================================================================
TEENCODE_DICT: dict[str, str] = {
    # Phủ định / khẳng định
    "k": "không",  "ko": "không",  "kg": "không",  "khg": "không",
    "kh": "không", "hok": "không", "hem": "không",  "hem có": "không có",
    "cx": "cũng",  "cg": "cũng",   "ck": "chồng",  "vk": "vợ",
    "ok": "được",  "oki": "được",  "oce": "được",   "dc": "được",
    "đc": "được",  "đk": "điều kiện", "dk": "điều kiện",

    # Đại từ / xưng hô
    "m": "mình",   "mk": "mình",   "mn": "mọi người", "mng": "mọi người",
    "t": "tôi",    "mk": "mình",   "bn": "bạn",    "bạn ơi": "bạn ơi",
    "ae": "anh em","a": "anh",     "e": "em",      "ib": "inbox",
    "bff": "bạn thân",

    # Thời gian
    "bh": "bây giờ", "bây h": "bây giờ", "gio": "giờ", "h": "giờ",
    "ng": "ngày",    "nay": "hôm nay",   "qua": "hôm qua",
    "s": "sau",      "trc": "trước",     "tg": "thời gian",
    "lm": "lâu mau",

    # Cảm xúc / trạng thái
    "thik": "thích",  "thk": "thích",  "yeu": "yêu",
    "buon": "buồn",   "vui": "vui",    "cool": "tuyệt",
    "haha": "haha",   "hihi": "hihi",  "hehe": "hehe",
    "lol": "buồn cười", "omg": "trời ơi", "wow": "tuyệt vời",
    "oke": "được",   "okee": "được",

    # Hành động
    "hỏi": "hỏi",   "rep": "trả lời", "cmt": "bình luận",
    "share": "chia sẻ", "like": "thích", "sub": "đăng ký",
    "follow": "theo dõi", "view": "xem", "tag": "gắn thẻ",

    # Địa điểm / tổ chức
    "tvu": "trường đại học trà vinh",
    "đhsv": "đại học sinh viên",
    "sv": "sinh viên",
    "gv": "giảng viên",
    "hs": "học sinh",
    "kt": "kinh tế",
    "ktx": "ký túc xá",
    "hp": "học phí",
    "hb": "học bổng",

    # Tính từ / trạng từ
    "vc": "vậy chứ",  "v": "vậy",    "vậy á": "vậy à",
    "r": "rồi",       "rồi á": "rồi à", "nha": "nhé",
    "nhe": "nhé",     "nhen": "nhé", "ha": "hả",
    "ah": "à",        "a": "à",      "ạ": "ạ",
    "oy": "ôi",       "oi": "ôi",    "trời": "trời",
    "đỉnh": "đỉnh",   "đính": "đính",
    "hay": "hay",     "tuyệt": "tuyệt",
    "chill": "thoải mái", "sad": "buồn", "hype": "hứng khởi",

    # Viết tắt phổ biến
    "sp": "sản phẩm",  "dv": "dịch vụ",   "ql": "quản lý",
    "nv": "nhân viên", "kh": "khách hàng","tl": "trả lời",
    "tks": "cảm ơn",   "ty": "cảm ơn",    "thx": "cảm ơn",
    "ths": "cảm ơn",   "cam on": "cảm ơn",
    "xin lỗi": "xin lỗi", "xl": "xin lỗi",
    "vl": "quá đáng",  "vcl": "quá đáng", "vcc": "quá đáng",

    # Trường đại học Trà Vinh cụ thể
    "trà vinh": "trà vinh",
    "travinh": "trà vinh",
    "đhtravinh": "đại học trà vinh",
    "daihoctravinh": "đại học trà vinh",
    "hottrend": "xu hướng",
    "viral": "lan truyền",
    "fyp": "trang dành cho bạn",
    "ontop": "nổi bật",
}

# ============================================================================
# TỪ ĐIỂN EMOJI → CẢM XÚC
# ============================================================================
EMOJI_SENTIMENT: dict[str, str] = {
    # Tích cực
    "😍": " rất thích ",  "🥰": " rất yêu ",    "😊": " vui ",
    "😄": " vui ",        "😁": " vui ",         "🤩": " tuyệt vời ",
    "👍": " tốt ",        "❤️": " yêu ",          "💕": " yêu ",
    "💯": " hoàn toàn đồng ý ", "🔥": " tuyệt ",  "✨": " tuyệt vời ",
    "🎉": " chúc mừng ",  "🥳": " vui mừng ",    "💪": " mạnh mẽ ",
    "🤗": " ôm hôn ",     "😘": " yêu ",         "💖": " yêu thích ",
    "🌟": " xuất sắc ",   "⭐": " tốt ",         "🏆": " giỏi nhất ",
    "👏": " tuyệt vời ",  "🙌": " tuyệt ",       "🥇": " xuất sắc ",

    # Tiêu cực
    "😢": " buồn ",       "😭": " rất buồn ",    "😤": " tức giận ",
    "😡": " tức giận ",   "🤬": " rất tức giận ","😒": " không hài lòng ",
    "😑": " thất vọng ",  "🙄": " khó chịu ",    "👎": " không tốt ",
    "😞": " thất vọng ",  "😔": " buồn ",        "😓": " mệt mỏi ",
    "💔": " đau lòng ",   "😰": " lo lắng ",     "😱": " sợ hãi ",

    # Trung tính / hài hước
    "😂": " hài hước ",   "🤣": " hài hước ",    "😆": " buồn cười ",
    "🤔": " suy nghĩ ",   "🤷": " không biết ",  "😅": " ngại ngùng ",
    "😐": " bình thường ","🙂": " bình thường ",  "😶": " không có gì ",
    "🫡": " tôn trọng ",  "🫢": " ngạc nhiên ",  "😮": " ngạc nhiên ",
}

# Comment không có giá trị phân tích
_LOW_VALUE_PATTERNS = [
    r"^[👍👎❤️🔥✨💯😍😊😄😁🤩🥰💕]*$",           # chỉ emoji
    r"^[.\s!?…•·*\-_]{1,10}$",                         # chỉ dấu câu
    r"^(ok|oke|oce|oki|okk|ok+|👍*|\.+|!!+)$",        # ok / dấu
    r"^\d+$",                                           # chỉ số
    r"^[a-zA-Z]{1,3}$",                                 # 1-3 ký tự latin
    r"^(haha+|hihi+|hehe+|huhu+|hix+|huh+)$",          # tiếng cười
    r"^(ờ+|ừ+|uh+|um+|hmm+|ah+|ơ+)$",                 # từ lấp đầy
]
_LOW_VALUE_RE = re.compile("|".join(_LOW_VALUE_PATTERNS), re.IGNORECASE | re.UNICODE)

# Ký tự lặp quá nhiều: "vui quáaaaa" → "vui quá"
_REPEAT_CHAR_RE = re.compile(r"(.)\1{2,}")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"(?<!\w)@[A-Za-z0-9._]+")
_HASHTAG_RE = re.compile(r"#([\w_]+)", re.UNICODE)
_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]")
_CONTROL_RE = re.compile(r"[\r\n\t]+")
_BASIC_SPECIAL_RE = re.compile(
    r"[^\w\sàáâãèéêìíòóôõùúýăđơưạảấầẩẫậắặẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵ"
    r"ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ!?.,:;\-/]",
    re.UNICODE,
)
_MODEL_SPECIAL_RE = re.compile(
    r"[^\w\sàáâãèéêìíòóôõùúýăđơưạảấầẩẫậắặẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵ"
    r"ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯ]",
    re.UNICODE,
)


# ============================================================================
# HÀM XỬ LÝ CHÍNH
# ============================================================================
def normalize_unicode(text: str) -> str:
    """Chuẩn hóa unicode về dạng NFC (tránh ký tự tổ hợp bị tách)."""
    return unicodedata.normalize("NFC", text)


def replace_emoji(text: str) -> str:
    """Thay emoji bằng mô tả cảm xúc tiếng Việt."""
    for emoji, meaning in EMOJI_SENTIMENT.items():
        text = text.replace(emoji, meaning)
    return text


def remove_emoji(text: str) -> str:
    """Xóa emoji phổ biến để dễ đọc hơn ở bước gán nhãn thủ công."""
    for emoji in EMOJI_SENTIMENT:
        text = text.replace(emoji, " ")
    return text


def remove_urls(text: str) -> str:
    """Xóa URL khỏi comment."""
    return _URL_RE.sub(" ", text)


def remove_mentions(text: str) -> str:
    """Xóa @tag / @username khỏi comment."""
    return _MENTION_RE.sub(" ", text)


def normalize_hashtags(text: str) -> str:
    """Giữ lại nội dung hashtag nhưng bỏ ký tự #."""
    return _HASHTAG_RE.sub(r" \1 ", text)


def strip_invisible_chars(text: str) -> str:
    """Loại ký tự zero-width và control characters."""
    text = _ZERO_WIDTH_RE.sub(" ", text)
    return _CONTROL_RE.sub(" ", text)


def strip_special_chars(text: str, keep_basic_punctuation: bool = False) -> str:
    """Loại ký tự lạ; dùng ít mạnh tay hơn ở bước gán nhãn thủ công."""
    pattern = _BASIC_SPECIAL_RE if keep_basic_punctuation else _MODEL_SPECIAL_RE
    return pattern.sub(" ", text)


def replace_teencode(text: str) -> str:
    """Thay teen-code bằng từ chuẩn. Ưu tiên cụm từ dài trước."""
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        # Thử 2-gram trước
        if i + 1 < len(words):
            bigram = f"{words[i]} {words[i+1]}".lower()
            if bigram in TEENCODE_DICT:
                result.append(TEENCODE_DICT[bigram])
                i += 2
                continue
        w = words[i].lower().strip(".,!?;:")
        result.append(TEENCODE_DICT.get(w, words[i]))
        i += 1
    return " ".join(result)


def normalize_repeated_chars(text: str) -> str:
    """Rút gọn ký tự lặp: 'quáaaaaaa' → 'quáa' (giữ 2 để giữ cảm xúc)."""
    return _REPEAT_CHAR_RE.sub(r"\1\1", text)


def normalize_whitespace(text: str) -> str:
    """Xóa khoảng trắng thừa."""
    return re.sub(r"\s+", " ", text).strip()


def is_low_value(text: str) -> bool:
    """Trả về True nếu comment không có giá trị phân tích."""
    clean = text.strip()
    if len(clean) < 2:
        return True
    return bool(_LOW_VALUE_RE.match(clean))


def basic_clean_text(text: str, remove_emojis: bool = True) -> str:
    """Làm sạch sơ bộ cho bước gán nhãn thủ công.

    Mục tiêu: comment dễ đọc hơn nhưng chưa chuẩn hóa sâu teen-code cho model.
    """
    if not text:
        return ""

    text = html.unescape(str(text))
    text = normalize_unicode(text)
    text = strip_invisible_chars(text)
    text = remove_urls(text)
    text = remove_mentions(text)
    text = normalize_hashtags(text)
    text = remove_emoji(text) if remove_emojis else text
    text = normalize_repeated_chars(text)
    text = strip_special_chars(text, keep_basic_punctuation=True)
    text = normalize_whitespace(text)
    return text


def preprocess(text: str, normalize_teen: bool = True, normalize_emojis: bool = True) -> str:
    """Pipeline tiền xử lý đầy đủ cho 1 comment.

    Args:
        text: Văn bản gốc.
        normalize_teen: Chuẩn hóa teen-code.
        normalize_emojis: Thay emoji bằng text.

    Returns:
        Văn bản đã làm sạch, hoặc chuỗi rỗng nếu comment vô giá trị.
    """
    if not text:
        return ""

    text = basic_clean_text(text, remove_emojis=not normalize_emojis)
    if normalize_emojis:
        text = replace_emoji(text)
    if normalize_teen:
        text = replace_teencode(text)
    text = normalize_repeated_chars(text)
    text = strip_special_chars(text, keep_basic_punctuation=False)
    text = normalize_whitespace(text)
    return text


def get_text_hash(text: str) -> str:
    """MD5 hash của text sau khi lowercase + strip (để detect duplicate)."""
    return md5(text.lower().strip().encode("utf-8")).hexdigest()


# ============================================================================
# XỬ LÝ BATCH
# ============================================================================
class TextPreprocessor:
    """Tiền xử lý toàn bộ danh sách comment, phát hiện duplicate."""

    def __init__(
        self,
        normalize_teen: bool = True,
        normalize_emojis: bool = True,
        remove_low_value: bool = True,
        remove_duplicates: bool = True,
    ):
        self.normalize_teen    = normalize_teen
        self.normalize_emojis  = normalize_emojis
        self.remove_low_value  = remove_low_value
        self.remove_duplicates = remove_duplicates

    def process_comments(self, comments: list[dict]) -> dict:
        """Xử lý danh sách comment dicts (mỗi dict có ít nhất key 'text').

        Returns:
            {
                'processed': [...],   # comment đã xử lý
                'removed_low_value': [...],
                'removed_duplicate': [...],
                'stats': {...}
            }
        """
        processed, removed_low, removed_dup = [], [], []
        seen_hashes: set[str] = set()

        for c in comments:
            original = c.get("text", "") or ""

            # Bước 1: low-value check trên text gốc
            if self.remove_low_value and is_low_value(original):
                removed_low.append({**c, "removal_reason": "low_value"})
                continue

            # Bước 2: tiền xử lý
            cleaned = preprocess(original, self.normalize_teen, self.normalize_emojis)

            # Bước 3: low-value check lại sau khi xử lý (emoji-only có thể thành whitespace)
            if self.remove_low_value and is_low_value(cleaned):
                removed_low.append({**c, "removal_reason": "low_value_after_clean"})
                continue

            # Bước 4: duplicate detection
            if self.remove_duplicates:
                h = get_text_hash(cleaned)
                if h in seen_hashes:
                    removed_dup.append({**c, "removal_reason": "duplicate"})
                    continue
                seen_hashes.add(h)

            processed.append({
                **c,
                "text_original": original,
                "text": cleaned,
                "preprocessed": True,
            })

        total = len(comments)
        kept  = len(processed)
        stats = {
            "total_input":        total,
            "kept":               kept,
            "removed_low_value":  len(removed_low),
            "removed_duplicate":  len(removed_dup),
            "reduction_rate_pct": round((total - kept) / total * 100, 1) if total else 0,
        }
        return {
            "processed":         processed,
            "removed_low_value": removed_low,
            "removed_duplicate": removed_dup,
            "stats":             stats,
        }

    def process_single(self, text: str) -> dict:
        """Xử lý 1 comment đơn lẻ, trả về dict kết quả."""
        original = text or ""
        low_value = self.remove_low_value and is_low_value(original)
        cleaned   = preprocess(original, self.normalize_teen, self.normalize_emojis) if not low_value else ""
        return {
            "original":  original,
            "cleaned":   cleaned,
            "low_value": low_value,
            "hash":      get_text_hash(cleaned) if cleaned else "",
        }
