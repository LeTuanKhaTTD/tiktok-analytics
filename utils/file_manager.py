"""
File Manager - Quản lý cấu trúc thư mục dữ liệu
Tổ chức theo: data/{platform}/{account_id}/{timestamp}/
"""
import os
import json
from datetime import datetime
from pathlib import Path


class DataManager:
    """Quản lý việc lưu trữ và tổ chức file dữ liệu"""
    
    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
    def get_save_path(self, platform, account_id, file_type, extension="json"):
        """
        Tạo đường dẫn lưu file có cấu trúc
        
        Args:
            platform: 'tiktok', 'youtube', 'facebook'
            account_id: username hoặc channel_id
            file_type: 'sentiment', 'metrics', 'comprehensive', 'videos'
            extension: 'json', 'csv', 'txt'
        
        Returns:
            Path object của file
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # Tạo cấu trúc thư mục: data/platform/account_id/timestamp/
        save_dir = self.base_dir / platform / account_id / timestamp
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Tên file
        filename = f"{file_type}.{extension}"
        filepath = save_dir / filename
        
        # Cập nhật symlink "latest"
        self._update_latest_link(platform, account_id, save_dir)
        
        return filepath, timestamp
    
    def _update_latest_link(self, platform, account_id, target_dir):
        """
        Tạo/cập nhật thư mục 'latest' trỏ đến phân tích mới nhất
        
        Note: Windows không hỗ trợ symlink tốt, dùng file marker thay thế
        """
        latest_marker = self.base_dir / platform / account_id / "latest.txt"
        
        try:
            with open(latest_marker, 'w', encoding='utf-8') as f:
                f.write(str(target_dir))
        except Exception as e:
            print(f"⚠️ Không thể tạo latest marker: {e}")
    
    def get_latest_analysis(self, platform, account_id):
        """
        Lấy thư mục phân tích mới nhất của account
        
        Returns:
            Path object hoặc None
        """
        latest_marker = self.base_dir / platform / account_id / "latest.txt"
        
        if latest_marker.exists():
            try:
                with open(latest_marker, 'r', encoding='utf-8') as f:
                    latest_path = Path(f.read().strip())
                    if latest_path.exists():
                        return latest_path
            except:
                pass
        
        # Fallback: Tìm thư mục mới nhất
        account_dir = self.base_dir / platform / account_id
        if not account_dir.exists():
            return None
        
        analyses = []
        for item in account_dir.iterdir():
            if item.is_dir() and item.name.replace('-', '').replace('_', '').isdigit():
                analyses.append(item)
        
        if analyses:
            return max(analyses, key=lambda x: x.name)
        
        return None
    
    def list_analyses(self, platform, account_id):
        """
        Liệt kê tất cả phân tích của 1 account
        
        Returns:
            List of dict với thông tin phân tích
        """
        account_dir = self.base_dir / platform / account_id
        if not account_dir.exists():
            return []
        
        analyses = []
        for item in account_dir.iterdir():
            if not item.is_dir():
                continue
            
            # Bỏ qua file marker
            if item.name == "latest.txt":
                continue
            
            # Chỉ lấy thư mục có format timestamp
            if not item.name.replace('-', '').replace('_', '').isdigit():
                continue
            
            # Lấy danh sách file trong thư mục
            files = {}
            for file in item.iterdir():
                if file.is_file():
                    file_type = file.stem  # Tên không có extension
                    files[file_type] = str(file)
            
            analyses.append({
                "timestamp": item.name,
                "path": str(item),
                "files": files
            })
        
        # Sắp xếp theo thời gian (mới nhất trước)
        return sorted(analyses, key=lambda x: x["timestamp"], reverse=True)
    
    def get_file_path(self, platform, account_id, timestamp, file_type):
        """
        Lấy đường dẫn của file cụ thể
        
        Returns:
            Path object hoặc None
        """
        file_dir = self.base_dir / platform / account_id / timestamp
        
        # Thử các extension phổ biến
        for ext in ['json', 'csv', 'txt']:
            filepath = file_dir / f"{file_type}.{ext}"
            if filepath.exists():
                return filepath
        
        return None
    
    def load_json(self, filepath):
        """Load file JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Lỗi load JSON {filepath}: {e}")
            return None
    
    def save_json(self, filepath, data, indent=2):
        """Lưu file JSON"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Lỗi lưu JSON {filepath}: {e}")
            return False
    
    def get_storage_stats(self):
        """Thống kê dung lượng lưu trữ"""
        stats = {
            "total_size_mb": 0,
            "platforms": {}
        }
        
        for platform_dir in self.base_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            
            platform_size = 0
            account_count = 0
            analysis_count = 0
            
            for account_dir in platform_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                
                account_count += 1
                
                for analysis_dir in account_dir.iterdir():
                    if not analysis_dir.is_dir():
                        continue
                    
                    analysis_count += 1
                    
                    # Tính dung lượng
                    for file in analysis_dir.rglob('*'):
                        if file.is_file():
                            platform_size += file.stat().st_size
            
            stats["platforms"][platform_dir.name] = {
                "size_mb": round(platform_size / 1024 / 1024, 2),
                "accounts": account_count,
                "analyses": analysis_count
            }
            
            stats["total_size_mb"] += platform_size
        
        stats["total_size_mb"] = round(stats["total_size_mb"] / 1024 / 1024, 2)
        
        return stats


if __name__ == "__main__":
    # Test
    dm = DataManager()
    
    # Test get save path
    filepath, timestamp = dm.get_save_path("tiktok", "travinhuniversity", "test")
    print(f"Save path: {filepath}")
    
    # Test save JSON
    test_data = {"message": "Hello World"}
    dm.save_json(filepath, test_data)
    
    # Test list analyses
    analyses = dm.list_analyses("tiktok", "travinhuniversity")
    print(f"\nAnalyses found: {len(analyses)}")
    for a in analyses[:3]:
        print(f"  - {a['timestamp']}")
    
    # Test storage stats
    stats = dm.get_storage_stats()
    print(f"\nStorage stats:")
    print(f"  Total: {stats['total_size_mb']} MB")
    for platform, pstats in stats['platforms'].items():
        print(f"  {platform}: {pstats['size_mb']} MB ({pstats['analyses']} analyses)")
