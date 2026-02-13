#!/usr/bin/env python3
"""
TNEA AI Configuration Validator
This script validates that all necessary components are properly configured
for the enhanced TNEA AI application to run correctly.
"""

import os
import sys
import json
from pathlib import Path

def validate_environment():
    """Validate environment configuration"""
    print("🔍 Validating Environment Configuration...")
    
    # Check if in correct directory
    required_files = ['.env', 'requirements.txt', 'src/', 'data/']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files/directories: {missing_files}")
        return False
    else:
        print("✅ All required files/directories present")
    
    # Check .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'NVIDIA_API_KEY=' in env_content:
                # Check if API key is set (not empty)
                for line in env_content.split('\n'):
                    if line.startswith('NVIDIA_API_KEY=') and len(line) > 15:
                        print("✅ NVIDIA_API_KEY is configured in .env")
                        break
                else:
                    print("⚠️  NVIDIA_API_KEY is not set in .env (will need to be set before running)")
            else:
                print("⚠️  NVIDIA_API_KEY not found in .env (will need to be added)")
    else:
        print("⚠️  .env file not found (copy .env.example and configure)")
    
    return True

def validate_dependencies():
    """Validate that all dependencies are available"""
    print("\n🔍 Validating Dependencies...")
    
    required_modules = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'), 
        ('sklearn', 'scikit-learn'),
        ('scipy', 'scipy'),
        ('requests', 'requests'),
        ('openai', 'openai'),
        ('streamlit', 'streamlit'),
        ('dotenv', 'python-dotenv'),
        ('plotly', 'plotly')
    ]
    
    missing_modules = []
    
    for import_name, display_name in required_modules:
        try:
            __import__(import_name)
            print(f"✅ {display_name} available")
        except ImportError:
            missing_modules.append(display_name)
    
    if missing_modules:
        print(f"❌ Missing modules: {missing_modules}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies available")
        return True

def validate_data_files():
    """Validate that all required data files are present"""
    print("\n🔍 Validating Data Files...")
    
    data_dir = Path('data')
    json_dir = data_dir / 'json'
    
    required_data_files = [
        'colleges.json',
        'cutoffs.json', 
        'seats.json',
        'branches.json',
        'college_geo_locations.json',
        'branch_trends.json',
        'predictions.json',
        'districts.json'
    ]
    
    missing_files = []
    
    if not json_dir.exists():
        print(f"❌ Data directory not found: {json_dir}")
        return False
    
    for file in required_data_files:
        if not (json_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing data files: {missing_files}")
        return False
    else:
        print("✅ All required data files present")
        
        # Check data file sizes
        for file in required_data_files[:3]:  # Check first 3 files
            file_path = json_dir / file
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"   📊 {file}: {size_mb:.2f} MB")
        
        return True

def validate_application_structure():
    """Validate application structure"""
    print("\n🔍 Validating Application Structure...")
    
    src_dir = Path('src')
    required_dirs = [
        'agent/',
        'ai/', 
        'data/',
        'logic/',
        'utils/',
        'tests/',
        'web/'
    ]
    
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not (src_dir / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ Missing source directories: {missing_dirs}")
        return False
    else:
        print("✅ All required source directories present")
    
    # Check for key application files
    key_files = [
        'agent/counsellor_agent.py',
        'llm_gateway.py',
        'config.py',
        'enhanced_streamlit_app.py',  # Our enhancement
        'run.py'
    ]
    
    missing_key_files = []
    for file in key_files:
        if not (src_dir / file).exists():
            missing_key_files.append(file)
    
    if missing_key_files:
        print(f"❌ Missing key application files: {missing_key_files}")
        return False
    else:
        print("✅ All key application files present")
        
    return True

def main():
    print("🎓 TNEA AI Enhanced Edition - Configuration Validator")
    print("=" * 55)
    
    all_valid = True
    
    all_valid &= validate_environment()
    all_valid &= validate_dependencies()
    all_valid &= validate_data_files()
    all_valid &= validate_application_structure()
    
    print(f"\n{'='*55}")
    if all_valid:
        print("🎉 All validations passed! The application is ready to run.")
        print("\n🚀 To launch the application:")
        print("   1. Ensure NVIDIA_API_KEY is set in .env")
        print("   2. Run: ./start.sh (for Enhanced GUI)")
        print("   3. Or: ./start.sh cli (for Enhanced CLI)")
    else:
        print("❌ Some validations failed. Please address the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()