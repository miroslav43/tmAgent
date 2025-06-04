#!/usr/bin/env python3
"""
Cleanup Script - Removes temporary files and cache
"""

import os
import shutil
from pathlib import Path

def cleanup_cache():
    """Remove Python cache files"""
    print("🧹 Cleaning Python cache...")
    
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            cache_dirs.append(cache_dir)
    
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"✓ Removed: {cache_dir}")
        except Exception as e:
            print(f"✗ Error removing {cache_dir}: {e}")
    
    if not cache_dirs:
        print("✓ No Python cache found")

def cleanup_temp_files():
    """Remove temporary files"""
    print("\n🧹 Cleaning temporary files...")
    
    temp_patterns = [
        "*.tmp",
        "*.temp", 
        "*.log",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    removed_count = 0
    for pattern in temp_patterns:
        for file_path in Path('.').rglob(pattern):
            try:
                file_path.unlink()
                print(f"✓ Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"✗ Error removing {file_path}: {e}")
    
    if removed_count == 0:
        print("✓ No temporary files found")

def cleanup_empty_dirs():
    """Remove empty directories in auxiliary folders"""
    print("\n🧹 Cleaning empty directories...")
    
    aux_dirs = ['data', 'logs', 'output']
    
    for aux_dir in aux_dirs:
        if os.path.exists(aux_dir):
            for root, dirs, files in os.walk(aux_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            print(f"✓ Removed empty directory: {dir_path}")
                    except Exception as e:
                        print(f"✗ Error removing {dir_path}: {e}")

def show_disk_usage():
    """Show disk usage of main directories"""
    print("\n📊 Disk Usage:")
    
    directories = [
        'datasets',
        'results',
        'scripts',
        'config'
    ]
    
    for dir_name in directories:
        if os.path.exists(dir_name):
            total_size = 0
            for root, dirs, files in os.walk(dir_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass
            
            # Convert to human readable format
            if total_size < 1024:
                size_str = f"{total_size} B"
            elif total_size < 1024**2:
                size_str = f"{total_size/1024:.1f} KB"
            elif total_size < 1024**3:
                size_str = f"{total_size/(1024**2):.1f} MB"
            else:
                size_str = f"{total_size/(1024**3):.1f} GB"
            
            print(f"📁 {dir_name}: {size_str}")

def main():
    """Main cleanup function"""
    print("🧹 HCL ANALYSIS PIPELINE - CLEANUP")
    print("=" * 50)
    
    cleanup_cache()
    cleanup_temp_files() 
    cleanup_empty_dirs()
    show_disk_usage()
    
    print("\n" + "=" * 50)
    print("✅ Cleanup completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 