from datetime import datetime


def build_report_summary(metrics: dict) -> str:
    return (
        f"Bao cao tu dong ngay {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        f"Tong phan tich: {metrics.get('total', 0)} | "
        f"Positive: {metrics.get('positive', 0)} | "
        f"Neutral: {metrics.get('neutral', 0)} | "
        f"Negative: {metrics.get('negative', 0)}"
    )
