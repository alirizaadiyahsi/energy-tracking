#!/usr/bin/env python3
"""
IoT Mock Service Setup and Quick Start

This script helps set up and test the IoT Mock Service
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("🚀 IoT Mock Service Setup")
    print("=" * 50)
    print("Welcome to the Energy Tracking IoT Mock Service!")
    print("This tool will help you set up and test the mock IoT service.")
    print()


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    return True


def check_docker():
    """Check if Docker is available"""
    print("\n🐳 Checking Docker...")
    
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker is available")
            print(f"   {result.stdout.strip()}")
            return True
        else:
            print("❌ Docker command failed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed or not in PATH")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def check_requirements():
    """Check if requirements.txt packages are available"""
    print("\n📦 Checking Python packages...")
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'pydantic',
        'paho-mqtt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📥 Installing missing packages...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages, check=True)
            print("✅ Packages installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages")
            print("   Try running: pip install -r requirements.txt")
            return False
    
    return True


def create_env_file():
    """Create .env file if it doesn't exist"""
    print("\n⚙️ Setting up configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        print("📋 Creating .env from .env.example...")
        try:
            content = env_example.read_text()
            env_file.write_text(content)
            print("✅ .env file created")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("⚠️ .env.example not found, creating basic .env...")
        basic_env = """# IoT Mock Service Configuration
HOST=0.0.0.0
PORT=8090
DEBUG=true
LOG_LEVEL=INFO
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=iot_user
MQTT_PASSWORD=iot123
SIMULATION_INTERVAL=5.0
"""
        try:
            env_file.write_text(basic_env)
            print("✅ Basic .env file created")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False


def start_service():
    """Start the service"""
    print("\n🚀 Starting IoT Mock Service...")
    
    try:
        print("   Starting service on http://localhost:8090")
        print("   Press Ctrl+C to stop the service")
        print("   Open another terminal to run tests")
        print()
        
        # Start the service
        subprocess.run([sys.executable, 'main.py'])
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Service stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting service: {e}")


def run_simple_test():
    """Run simple API test"""
    print("\n🧪 Running simple API test...")
    
    try:
        result = subprocess.run([sys.executable, 'simple_test.py'], 
                              capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def show_next_steps():
    """Show next steps"""
    print("\n🎯 Next Steps:")
    print("-" * 20)
    print("1. 🚀 Start the service:")
    print("   python main.py")
    print()
    print("2. 🧪 Test the service (in another terminal):")
    print("   python simple_test.py")
    print()
    print("3. 🌐 Access the API:")
    print("   - Service: http://localhost:8090")
    print("   - API Docs: http://localhost:8090/docs")
    print("   - Health: http://localhost:8090/health")
    print()
    print("4. 🐳 Using Docker (from project root):")
    print("   cd ../../docker")
    print("   docker-compose up -d iot-mock")
    print()
    print("💡 For help, check the README.md file")


def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        print("\n❌ Setup failed: Python version not supported")
        return 1
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the iot-mock service directory")
        return 1
    
    # Optional Docker check
    docker_available = check_docker()
    
    # Check and install Python packages
    if not check_requirements():
        print("\n❌ Setup failed: Could not install required packages")
        return 1
    
    # Create configuration
    if not create_env_file():
        print("\n❌ Setup failed: Could not create configuration")
        return 1
    
    print("\n✅ Setup completed successfully!")
    
    # Ask user what to do next
    print("\nWhat would you like to do?")
    print("1. Start the service now")
    print("2. Run API test (service must be running)")
    print("3. Show next steps and exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            start_service()
        elif choice == "2":
            success = run_simple_test()
            if success:
                print("\n🎉 All tests passed!")
            else:
                print("\n⚠️ Some tests failed. Make sure the service is running.")
        elif choice == "3":
            show_next_steps()
        else:
            print("Invalid choice. Showing next steps...")
            show_next_steps()
            
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted by user")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
