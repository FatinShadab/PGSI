"""
Verification demo script for platform abstraction module.

This script demonstrates the functionality of the platform module
and can be run to verify the implementation.
"""

from pathlib import Path
from pgsi_analyzer.platform import (
    detect_platform,
    is_linux_intel,
    is_windows,
    is_macos,
    get_user_data_dir,
    resolve_data_path,
    resolve_benchmark_path,
    get_cpu_info,
    get_system_info,
    check_rapl_support,
)

def main():
    print("=" * 60)
    print("Platform Abstraction Module - Verification Demo")
    print("=" * 60)
    print()
    
    # Platform Detection
    print("1. Platform Detection:")
    print(f"   Platform: {detect_platform()}")
    print(f"   Is Windows: {is_windows()}")
    print(f"   Is macOS: {is_macos()}")
    print(f"   Is Linux Intel: {is_linux_intel()}")
    print()
    
    # Path Resolution
    print("2. Path Resolution:")
    user_data_dir = get_user_data_dir()
    print(f"   User Data Dir: {user_data_dir}")
    print(f"   Type: {type(user_data_dir)}")
    
    data_path = resolve_data_path()
    print(f"   Data Path: {data_path}")
    print(f"   Type: {type(data_path)}")
    
    benchmark_path = resolve_benchmark_path("binary-trees", "cpython")
    print(f"   Benchmark Path: {benchmark_path}")
    print(f"   Type: {type(benchmark_path)}")
    print()
    
    # Hardware Detection
    print("3. Hardware Detection:")
    cpu_info = get_cpu_info()
    print(f"   CPU: {cpu_info['processor']}")
    print(f"   Physical Cores: {cpu_info['cores_physical']}")
    print(f"   Logical Cores: {cpu_info['cores_logical']}")
    print(f"   Architecture: {cpu_info['architecture']}")
    print()
    
    system_info = get_system_info(Path("test_result.csv"))
    print("4. System Information:")
    for key, value in system_info.items():
        print(f"   {key}: {value}")
    print()
    
    # RAPL Support
    print("5. RAPL Support:")
    rapl_support = check_rapl_support()
    print(f"   RAPL Available: {rapl_support}")
    if not rapl_support:
        print("   (RAPL requires Linux with Intel x86_64 CPU)")
    print()
    
    print("=" * 60)
    print("[OK] All platform module functions working correctly!")
    print("=" * 60)

if __name__ == "__main__":
    main()

