#!/usr/bin/env python3
"""
Database initialization script for RAG Demo
"""
import sys
import os
import asyncio
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).parent.parent))

from backend.models.database import init_db, get_db, Config
from backend.core.config import get_settings
from backend.utils.auth import get_password_hash

def main():
    """Initialize database with default configuration"""
    
    print("🚀 Initializing RAG Demo database...")
    
    try:
        # Initialize database tables
        init_db()
        print("✅ Database tables created")
        
        # Set up default admin password if not configured
        settings = get_settings()
        
        if settings.admin_password_hash == "$2b$12$your-bcrypt-hash-here":
            print("⚠️  Setting default admin password (change this in production!)")
            
            # Generate hash for default password "admin123"
            default_password = "admin123"
            password_hash = get_password_hash(default_password)
            
            print(f"Default admin password: {default_password}")
            print(f"Password hash: {password_hash}")
            print("Update your .env file with this hash!")
        
        # Create necessary directories
        directories = [
            "data/pdfs",
            "data/images", 
            "data/chunks",
            "data/chroma",
            "models",
            "prompts"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        
        # Create system prompt file
        system_prompt_path = "prompts/system_prompt.txt"
        if not os.path.exists(system_prompt_path):
            with open(system_prompt_path, 'w') as f:
                f.write("""You are an IT support assistant powered by RAG Demo. Your mission is to synthesize information from retrieved documentation chunks and their associated screenshots into clear, accurate, and actionable technical support responses.

PRIME DIRECTIVE: RETRIEVAL-AUGMENTED GENERATION

1. Absolute Grounding
- You MUST base your entire response exclusively on the information contained within the retrieved context chunks provided to you
- These chunks and their associated images are your sole source of truth
- You are forbidden from using your pre-trained knowledge about IT systems

2. Response Format
- Start directly with a descriptive H3 title: ### Resetting Windows Password
- Use numbered lists (1., 2., 3.) for main action sequences
- Use bullet points (*) for sub-steps, options, or clarifications
- Use backticks for `commands`, `filenames`, `/paths/`, `values`
- Use **bold** only for warnings, critical notes, or key concepts

3. Image Integration
- When chunks have associated images, reference them using: ![description](filename)
- Place image references immediately after the relevant text they illustrate

4. Citations
- Place citation numbers [1], [2, 4] at the end of each step or significant statement
- Citations go AFTER image references

Example response format:
### Configuring Static IP Address in Windows

1. Open `Control Panel > Network and Internet > Network Connections` [1]
   ![Network Connections window displaying all network adapters](network_connections.png)

2. Right-click your active network adapter and select **Properties** [1]
   ![Adapter context menu with Properties highlighted](adapter_menu.png)

3. Select **Internet Protocol Version 4 (TCP/IPv4)** and click **Properties** [2]""")
            print(f"✅ Created system prompt file: {system_prompt_path}")
        
        print("\\n🎉 Database initialization complete!")
        print("\\n📋 Next steps:")
        print("1. Update your .env file with proper configuration")
        print("2. Download the Mistral 7B model to ./models/")
        print("3. Start the backend server: uvicorn backend.api.main:app --reload")
        print("4. Upload PDF documents via the admin panel")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()