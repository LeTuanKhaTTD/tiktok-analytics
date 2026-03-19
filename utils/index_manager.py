"""
Index Manager - Quản lý index của tất cả phân tích
Tạo file INDEX.json để dễ dàng tìm kiếm và tracking
"""
import json
from datetime import datetime
from pathlib import Path


class IndexManager:
    """Quản lý file INDEX.json - master index của tất cả phân tích"""
    
    def __init__(self, index_file="data/INDEX.json"):
        self.index_file = Path(index_file)
        self.index = self._load_index()
    
    def _load_index(self):
        """Load index hiện tại"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Lỗi load index: {e}")
                return self._create_empty_index()
        
        return self._create_empty_index()
    
    def _create_empty_index(self):
        """Tạo index rỗng"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_analyses": 0,
            "analyses": []
        }
    
    def _save_index(self):
        """Lưu index"""
        try:
            self.index["last_updated"] = datetime.now().isoformat()
            self.index["total_analyses"] = len(self.index["analyses"])
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Lỗi lưu index: {e}")
            return False
    
    def add_analysis(self, platform, account_id, account_name, timestamp, files, metadata=None):
        """
        Thêm 1 phân tích vào index
        
        Args:
            platform: 'tiktok', 'youtube', 'facebook'
            account_id: username hoặc channel_id
            account_name: Tên hiển thị của account
            timestamp: Timestamp của phân tích (format: YYYY-MM-DD_HHMMSS)
            files: Dict các file đã tạo {type: path}
            metadata: Thông tin thêm (optional)
        
        Returns:
            ID của entry vừa thêm
        """
        entry_id = len(self.index["analyses"]) + 1
        
        entry = {
            "id": entry_id,
            "platform": platform,
            "account_id": account_id,
            "account_name": account_name,
            "timestamp": timestamp,
            "created_at": datetime.now().isoformat(),
            "files": files,
            "metadata": metadata or {},
            "tags": []
        }
        
        # Thêm vào đầu list (mới nhất trước)
        self.index["analyses"].insert(0, entry)
        
        # Lưu index
        self._save_index()
        
        return entry_id
    
    def update_analysis(self, entry_id, **kwargs):
        """Cập nhật thông tin của 1 phân tích"""
        for entry in self.index["analyses"]:
            if entry["id"] == entry_id:
                entry.update(kwargs)
                self._save_index()
                return True
        
        return False
    
    def add_tags(self, entry_id, tags):
        """Thêm tags cho phân tích"""
        if not isinstance(tags, list):
            tags = [tags]
        
        for entry in self.index["analyses"]:
            if entry["id"] == entry_id:
                entry["tags"].extend(tags)
                entry["tags"] = list(set(entry["tags"]))  # Remove duplicates
                self._save_index()
                return True
        
        return False
    
    def search(self, platform=None, account_id=None, date_from=None, date_to=None, tags=None):
        """
        Tìm kiếm phân tích theo điều kiện
        
        Args:
            platform: Lọc theo platform
            account_id: Lọc theo account
            date_from: Lọc từ ngày (ISO format)
            date_to: Lọc đến ngày (ISO format)
            tags: Lọc theo tags (list)
        
        Returns:
            List các phân tích khớp điều kiện
        """
        results = self.index["analyses"]
        
        # Filter by platform
        if platform:
            results = [r for r in results if r["platform"] == platform]
        
        # Filter by account
        if account_id:
            results = [r for r in results if r["account_id"] == account_id]
        
        # Filter by date range
        if date_from:
            results = [r for r in results if r["created_at"] >= date_from]
        
        if date_to:
            results = [r for r in results if r["created_at"] <= date_to]
        
        # Filter by tags
        if tags:
            if not isinstance(tags, list):
                tags = [tags]
            results = [r for r in results 
                      if any(tag in r.get("tags", []) for tag in tags)]
        
        return results
    
    def get_analysis_by_id(self, entry_id):
        """Lấy thông tin phân tích theo ID"""
        for entry in self.index["analyses"]:
            if entry["id"] == entry_id:
                return entry
        
        return None
    
    def get_latest_analysis(self, platform=None, account_id=None):
        """Lấy phân tích mới nhất"""
        results = self.search(platform=platform, account_id=account_id)
        
        if results:
            return results[0]  # Đã sort mới nhất trước
        
        return None
    
    def get_statistics(self):
        """Thống kê tổng quan"""
        stats = {
            "total_analyses": len(self.index["analyses"]),
            "platforms": {},
            "accounts": {},
            "recent_analyses": []
        }
        
        # Thống kê theo platform
        for entry in self.index["analyses"]:
            platform = entry["platform"]
            account = entry["account_id"]
            
            if platform not in stats["platforms"]:
                stats["platforms"][platform] = 0
            stats["platforms"][platform] += 1
            
            if account not in stats["accounts"]:
                stats["accounts"][account] = {
                    "platform": platform,
                    "account_name": entry["account_name"],
                    "count": 0
                }
            stats["accounts"][account]["count"] += 1
        
        # 10 phân tích gần nhất
        stats["recent_analyses"] = [
            {
                "id": e["id"],
                "platform": e["platform"],
                "account": e["account_name"],
                "timestamp": e["timestamp"]
            }
            for e in self.index["analyses"][:10]
        ]
        
        return stats
    
    def delete_analysis(self, entry_id):
        """Xóa phân tích khỏi index"""
        self.index["analyses"] = [
            e for e in self.index["analyses"] 
            if e["id"] != entry_id
        ]
        
        self._save_index()
    
    def rebuild_index(self, data_manager):
        """
        Rebuild lại index từ dữ liệu thực tế trong thư mục data
        
        Args:
            data_manager: Instance của DataManager
        """
        print("🔄 Đang rebuild index...")
        
        self.index = self._create_empty_index()
        
        # Scan toàn bộ thư mục data
        base_dir = Path(data_manager.base_dir)
        
        entry_id = 1
        for platform_dir in base_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            
            platform = platform_dir.name
            
            for account_dir in platform_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                
                account_id = account_dir.name
                
                for analysis_dir in account_dir.iterdir():
                    if not analysis_dir.is_dir():
                        continue
                    
                    # Bỏ qua file marker
                    if analysis_dir.name.endswith('.txt'):
                        continue
                    
                    timestamp = analysis_dir.name
                    
                    # Lấy danh sách file
                    files = {}
                    for file in analysis_dir.iterdir():
                        if file.is_file():
                            file_type = file.stem
                            files[file_type] = str(file)
                    
                    if not files:
                        continue
                    
                    # Thêm vào index
                    entry = {
                        "id": entry_id,
                        "platform": platform,
                        "account_id": account_id,
                        "account_name": account_id,  # Sẽ cập nhật sau nếu có
                        "timestamp": timestamp,
                        "created_at": datetime.now().isoformat(),
                        "files": files,
                        "metadata": {},
                        "tags": ["auto_imported"]
                    }
                    
                    self.index["analyses"].append(entry)
                    entry_id += 1
        
        # Sort theo timestamp mới nhất
        self.index["analyses"].sort(
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        
        # Lưu index
        self._save_index()
        
        print(f"✅ Rebuild hoàn tất: {len(self.index['analyses'])} phân tích")
        
        return len(self.index["analyses"])


if __name__ == "__main__":
    # Test
    im = IndexManager()
    
    # Test add analysis
    entry_id = im.add_analysis(
        platform="tiktok",
        account_id="travinhuniversity",
        account_name="@travinhuniversity",
        timestamp="2026-03-04_100000",
        files={
            "comprehensive": "data/tiktok/travinhuniversity/2026-03-04_100000/comprehensive.json"
        },
        metadata={"videos_count": 31}
    )
    
    print(f"Added entry: {entry_id}")
    
    # Test search
    results = im.search(platform="tiktok")
    print(f"\nTikTok analyses: {len(results)}")
    
    # Test statistics
    stats = im.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total: {stats['total_analyses']}")
    print(f"  Platforms: {stats['platforms']}")
