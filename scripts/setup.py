#!/usr/bin/env python3
"""
Setup script for the Lunia WhatsApp Agent
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from example...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created. Please update it with your actual configuration.")
    elif env_file.exists():
        print("✅ .env file already exists.")
    else:
        print("❌ .env.example file not found.")

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/lunia_info",
        "storage/vector_store",
        "storage/cache",
        "logs",
        "tests/unit",
        "tests/integration",
        "tests/e2e"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created.")

def create_sample_data():
    """Create sample data files if they don't exist"""
    data_dir = Path("data/lunia_info")
    
    # Create sample about.txt
    about_file = data_dir / "about.txt"
    if not about_file.exists():
        about_content = """Lunia Soluciones - AI Consulting Experts

We are a leading AI consulting company specializing in:
- AI strategy development
- Machine learning implementation
- Data analytics solutions
- AI-powered automation
- Custom AI applications

Our team of experts helps businesses transform their operations through intelligent automation and data-driven insights.

Founded in 2023, we have helped over 100 companies implement successful AI solutions across various industries including healthcare, finance, retail, and manufacturing.

Contact us to learn how AI can transform your business."""
        
        with open(about_file, 'w', encoding='utf-8') as f:
            f.write(about_content)
    
    # Create sample services.txt
    services_file = data_dir / "services.txt"
    if not services_file.exists():
        services_content = """Lunia Soluciones Services

AI STRATEGY CONSULTING
- AI readiness assessment
- Strategic AI roadmap development
- ROI analysis and business case development
- Technology selection and vendor evaluation

MACHINE LEARNING SOLUTIONS
- Custom ML model development
- Predictive analytics
- Computer vision applications
- Natural language processing
- Recommendation systems

DATA ANALYTICS
- Data warehouse design
- Business intelligence solutions
- Real-time analytics dashboards
- Data visualization and reporting

AI AUTOMATION
- Process automation using AI
- Intelligent document processing
- Chatbots and virtual assistants
- Workflow optimization

TRAINING & SUPPORT
- AI literacy training for teams
- Technical workshops
- Ongoing support and maintenance
- Performance monitoring and optimization

Contact us for a free consultation to discuss your AI needs."""
        
        with open(services_file, 'w', encoding='utf-8') as f:
            f.write(services_content)
    
    # Create sample FAQ
    faq_file = data_dir / "faq.txt"
    if not faq_file.exists():
        faq_content = """Frequently Asked Questions - Lunia Soluciones

Q: What industries do you serve?
A: We work with companies across all industries including healthcare, finance, retail, manufacturing, logistics, and more. Our AI solutions are adaptable to any business context.

Q: How long does a typical AI project take?
A: Project timelines vary depending on complexity. Simple automation projects may take 2-4 weeks, while comprehensive AI strategy implementations can take 3-6 months.

Q: Do you provide ongoing support?
A: Yes, we offer comprehensive support packages including monitoring, maintenance, updates, and performance optimization to ensure your AI solutions continue to deliver value.

Q: What's the minimum budget for an AI project?
A: We work with budgets starting from $10,000 for basic automation projects. Enterprise solutions typically range from $50,000 to $500,000+ depending on scope.

Q: Do you work with small businesses?
A: Absolutely! We have solutions designed specifically for small and medium businesses, including affordable AI automation tools and consulting packages.

Q: How do I get started?
A: Contact us for a free initial consultation. We'll assess your needs, discuss potential solutions, and provide a clear roadmap for implementation.

Q: Do you provide training for our team?
A: Yes, we offer comprehensive training programs to help your team understand and effectively use AI solutions. Training is customized to your specific needs and technical level."""
        
        with open(faq_file, 'w', encoding='utf-8') as f:
            f.write(faq_content)
    
    print("✅ Sample data files created.")

def check_dependencies():
    """Check if Poetry is installed"""
    try:
        import subprocess
        result = subprocess.run(['poetry', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Poetry is installed.")
            return True
        else:
            print("❌ Poetry is not installed or not in PATH.")
            return False
    except FileNotFoundError:
        print("❌ Poetry is not installed.")
        return False

def install_dependencies():
    """Install dependencies using Poetry"""
    print("Installing dependencies...")
    os.system("poetry install")
    print("✅ Dependencies installed.")

def main():
    """Main setup function"""
    print("🚀 Setting up Lunia WhatsApp Agent...")
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Create necessary files and directories
    create_directories()
    create_env_file()
    create_sample_data()
    
    # Check dependencies
    if check_dependencies():
        install_dependencies()
    else:
        print("Please install Poetry first: https://python-poetry.org/docs/#installation")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Update the .env file with your actual API keys and configuration")
    print("2. Add your company information to the files in data/lunia_info/")
    print("3. Run the application: poetry run python -m src.api.main")
    print("4. Test the webhook endpoint at http://localhost:8000/webhook/whatsapp")

if __name__ == "__main__":
    main()
