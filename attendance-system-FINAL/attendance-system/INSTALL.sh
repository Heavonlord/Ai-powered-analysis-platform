#!/bin/bash
# AttendAI — Quick Setup Script

echo "╔══════════════════════════════════════╗"
echo "║   AttendAI — Setup Script            ║"
echo "╚══════════════════════════════════════╝"

# Check Python
python3 --version || { echo "❌ Python 3 required"; exit 1; }

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate || { source venv/Scripts/activate 2>/dev/null; }

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Setup environment
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚙️  Created .env — edit it with your credentials"
fi

# Create instance directory
mkdir -p instance

# Initialize database and create admin
echo "🗄️  Setting up database..."
python create_admin.py --seed

echo ""
echo "✅ Setup complete!"
echo ""
echo "▶  Run the app:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "🌐 Open: http://localhost:5000"
echo ""
echo "Demo accounts:"
echo "   Admin:   admin / admin123"
echo "   Teacher: teacher1 / teacher123"
echo "   Student: student1 / student123"
