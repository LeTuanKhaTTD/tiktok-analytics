"""
Data Cleaner - Dọn dẹp và quản lý dữ liệu cũ
Tự động xóa file cũ, archive, optimize storage
"""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta


class DataCleaner:
    """Quản lý việc dọn dẹp dữ liệu cũ"""
    
    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)
        self.archive_dir = self.base_dir / "archives"
        self.archive_dir.mkdir(exist_ok=True)
    
    def cleanup_old_files(self, days=30, keep_latest=3, dry_run=False):
        """
        Xóa file cũ hơn X ngày, giữ lại Y file gần nhất
        
        Args:
            days: Xóa file cũ hơn bao nhiêu ngày
            keep_latest: Luôn giữ X file gần nhất (mỗi account)
            dry_run: True = chỉ show, không xóa thật
        
        Returns:
            Dict thống kê số file đã xóa
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stats = {
            "scanned": 0,
            "deleted": 0,
            "kept": 0,
            "freed_mb": 0,
            "errors": []
        }
        
        print(f"🧹 Dọn dẹp file cũ hơn {days} ngày...")
        print(f"   Giữ lại {keep_latest} phân tích gần nhất mỗi account")
        if dry_run:
            print("   [DRY RUN MODE - Không xóa thật]")
        
        for platform_dir in self.base_dir.iterdir():
            if not platform_dir.is_dir() or platform_dir.name == "archives":
                continue
            
            print(f"\n📱 Platform: {platform_dir.name}")
            
            for account_dir in platform_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                
                print(f"  👤 Account: {account_dir.name}")
                
                # Lấy danh sách phân tích, sort theo timestamp
                analyses = []
                for analysis_dir in account_dir.iterdir():
                    if not analysis_dir.is_dir():
                        continue
                    
                    # Bỏ qua marker files
                    if analysis_dir.name.endswith('.txt'):
                        continue
                    
                    # Parse timestamp
                    try:
                        timestamp_str = analysis_dir.name
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")
                        
                        # Tính dung lượng
                        size = sum(
                            f.stat().st_size 
                            for f in analysis_dir.rglob('*') 
                            if f.is_file()
                        )
                        
                        analyses.append({
                            "path": analysis_dir,
                            "timestamp": timestamp,
                            "size": size
                        })
                        
                        stats["scanned"] += 1
                    except Exception as e:
                        stats["errors"].append(f"Parse error: {analysis_dir.name} - {e}")
                        continue
                
                # Sort theo timestamp (mới nhất trước)
                analyses.sort(key=lambda x: x["timestamp"], reverse=True)
                
                # Giữ lại keep_latest file gần nhất
                kept = analyses[:keep_latest]
                candidates = analyses[keep_latest:]
                
                print(f"    📊 {len(analyses)} phân tích, giữ {len(kept)}, xét {len(candidates)}")
                
                # Xét các file còn lại
                for analysis in candidates:
                    if analysis["timestamp"] < cutoff_date:
                        size_mb = analysis["size"] / 1024 / 1024
                        
                        if dry_run:
                            print(f"    🗑️  [DRY RUN] Xóa: {analysis['path'].name} ({size_mb:.2f} MB)")
                        else:
                            try:
                                shutil.rmtree(analysis["path"])
                                print(f"    ✅ Đã xóa: {analysis['path'].name} ({size_mb:.2f} MB)")
                                stats["deleted"] += 1
                                stats["freed_mb"] += size_mb
                            except Exception as e:
                                error_msg = f"Delete error: {analysis['path'].name} - {e}"
                                stats["errors"].append(error_msg)
                                print(f"    ❌ {error_msg}")
                    else:
                        stats["kept"] += 1
        
        print(f"\n{'='*60}")
        print(f"📊 KẾT QUẢ:")
        print(f"  • Đã quét: {stats['scanned']} phân tích")
        print(f"  • Đã xóa: {stats['deleted']} phân tích")
        print(f"  • Giữ lại: {stats['kept']} phân tích")
        print(f"  • Dung lượng giải phóng: {stats['freed_mb']:.2f} MB")
        
        if stats["errors"]:
            print(f"  ⚠️  Lỗi: {len(stats['errors'])}")
            for err in stats["errors"][:5]:
                print(f"      - {err}")
        
        return stats
    
    def archive_old_data(self, days=90, delete_after_archive=True):
        """
        Nén file cũ thành .zip để tiết kiệm dung lượng
        
        Args:
            days: Archive file cũ hơn bao nhiêu ngày
            delete_after_archive: Xóa file gốc sau khi archive
        
        Returns:
            List các file archive đã tạo
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        archived_files = []
        
        print(f"📦 Archive dữ liệu cũ hơn {days} ngày...")
        
        for platform_dir in self.base_dir.iterdir():
            if not platform_dir.is_dir() or platform_dir.name == "archives":
                continue
            
            for account_dir in platform_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                
                # Tạo archive file
                archive_name = f"{platform_dir.name}_{account_dir.name}_{datetime.now().strftime('%Y%m')}.zip"
                archive_path = self.archive_dir / archive_name
                
                archived_count = 0
                
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for analysis_dir in account_dir.iterdir():
                        if not analysis_dir.is_dir():
                            continue
                        
                        try:
                            timestamp = datetime.strptime(
                                analysis_dir.name, 
                                "%Y-%m-%d_%H%M%S"
                            )
                            
                            if timestamp < cutoff_date:
                                # Thêm vào archive
                                for file in analysis_dir.rglob('*'):
                                    if file.is_file():
                                        arcname = str(file.relative_to(self.base_dir))
                                        zipf.write(file, arcname)
                                
                                archived_count += 1
                                
                                # Xóa thư mục gốc
                                if delete_after_archive:
                                    shutil.rmtree(analysis_dir)
                        
                        except Exception as e:
                            print(f"  ⚠️  Lỗi archive {analysis_dir.name}: {e}")
                            continue
                
                if archived_count > 0:
                    archive_size = archive_path.stat().st_size / 1024 / 1024
                    print(f"  ✅ {archive_name}: {archived_count} phân tích ({archive_size:.2f} MB)")
                    archived_files.append(str(archive_path))
                else:
                    # Xóa archive rỗng
                    archive_path.unlink()
        
        print(f"\n📦 Đã tạo {len(archived_files)} archive files")
        
        return archived_files
    
    def get_disk_usage(self):
        """Thống kê dung lượng đĩa"""
        stats = {
            "total_mb": 0,
            "platforms": {},
            "oldest_analysis": None,
            "newest_analysis": None
        }
        
        oldest_date = None
        newest_date = None
        
        for platform_dir in self.base_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            
            platform_size = 0
            analysis_count = 0
            
            for account_dir in platform_dir.iterdir():
                if not account_dir.is_dir():
                    continue
                
                for analysis_dir in account_dir.iterdir():
                    if not analysis_dir.is_dir():
                        continue
                    
                    try:
                        timestamp = datetime.strptime(
                            analysis_dir.name,
                            "%Y-%m-%d_%H%M%S"
                        )
                        
                        # Track oldest/newest
                        if oldest_date is None or timestamp < oldest_date:
                            oldest_date = timestamp
                            stats["oldest_analysis"] = analysis_dir.name
                        
                        if newest_date is None or timestamp > newest_date:
                            newest_date = timestamp
                            stats["newest_analysis"] = analysis_dir.name
                    except:
                        pass
                    
                    # Tính dung lượng
                    for file in analysis_dir.rglob('*'):
                        if file.is_file():
                            platform_size += file.stat().st_size
                    
                    analysis_count += 1
            
            stats["platforms"][platform_dir.name] = {
                "size_mb": round(platform_size / 1024 / 1024, 2),
                "analyses": analysis_count
            }
            
            stats["total_mb"] += platform_size
        
        stats["total_mb"] = round(stats["total_mb"] / 1024 / 1024, 2)
        
        return stats
    
    def optimize_storage(self, days=30, keep_latest=5):
        """
        Tối ưu hóa storage tổng hợp
        - Cleanup old files
        - Archive very old files
        - Show statistics
        """
        print("🚀 BẮT ĐẦU TỐI ƯU HÓA STORAGE")
        print("="*60)
        
        # 1. Show current usage
        print("\n📊 DUNG LƯỢNG HIỆN TẠI:")
        usage = self.get_disk_usage()
        print(f"  Total: {usage['total_mb']} MB")
        for platform, stats in usage['platforms'].items():
            print(f"  • {platform}: {stats['size_mb']} MB ({stats['analyses']} analyses)")
        
        # 2. Cleanup old files
        print(f"\n🧹 BƯỚC 1: XÓA FILE CŨ HƠN {days} NGÀY")
        print("-"*60)
        cleanup_stats = self.cleanup_old_files(days=days, keep_latest=keep_latest)
        
        # 3. Archive very old files (90+ days)
        if days < 90:
            print(f"\n📦 BƯỚC 2: ARCHIVE FILE CŨ HƠN 90 NGÀY")
            print("-"*60)
            archived = self.archive_old_data(days=90, delete_after_archive=True)
        
        # 4. Show final usage
        print(f"\n📊 DUNG LƯỢNG SAU TỐI ƯU:")
        print("-"*60)
        final_usage = self.get_disk_usage()
        print(f"  Total: {final_usage['total_mb']} MB")
        saved_mb = usage['total_mb'] - final_usage['total_mb']
        print(f"  Đã tiết kiệm: {saved_mb:.2f} MB")
        
        print("\n✅ HOÀN TẤT TỐI ƯU HÓA!")


if __name__ == "__main__":
    # Test
    cleaner = DataCleaner()
    
    # Test disk usage
    print("📊 Disk Usage:")
    usage = cleaner.get_disk_usage()
    print(f"  Total: {usage['total_mb']} MB")
    print(f"  Oldest: {usage['oldest_analysis']}")
    print(f"  Newest: {usage['newest_analysis']}")
    
    # Test cleanup (dry run)
    print("\n🧹 Cleanup Test (Dry Run):")
    stats = cleaner.cleanup_old_files(days=30, keep_latest=3, dry_run=True)
