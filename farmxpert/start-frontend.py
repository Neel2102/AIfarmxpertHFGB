#!/usr/bin/env python3
"""
FarmXpert Frontend Startup Script
Run this to start the React frontend development server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_node_installation():
    """Check if Node.js and npm are installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found!")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found! Please install Node.js 16+ from https://nodejs.org/")
        return False
    
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
        else:
            print("❌ npm not found!")
            return False
    except FileNotFoundError:
        print("❌ npm not found! Please install npm")
        return False
    
    return True

def install_dependencies():
    """Install frontend dependencies"""
    print("📦 Installing frontend dependencies...")
    try:
        subprocess.run(['npm', 'install'], check=True, cwd='frontend')
        print("✅ Frontend dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install frontend dependencies")
        return False

def start_frontend():
    """Start the React development server"""
    print("🚀 Starting FarmXpert Frontend...")
    print("📍 Frontend will be available at: http://localhost:3000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run(['npm', 'start'], check=True, cwd='frontend')
    except KeyboardInterrupt:
        print("\n👋 FarmXpert frontend stopped!")
    except subprocess.CalledProcessError:
        print("❌ Failed to start frontend server")

def main():
    """Main startup function"""
    print("🌾 Welcome to FarmXpert Frontend!")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("frontend/package.json").exists():
        print("❌ Please run this script from the farmxpert directory")
        sys.exit(1)
    
    # Check Node.js installation
    if not check_node_installation():
        print("\n📋 Next steps:")
        print("1. Install Node.js 16+ from https://nodejs.org/")
        print("2. Run this script again")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Start frontend
    start_frontend()

if __name__ == "__main__":
    main()
