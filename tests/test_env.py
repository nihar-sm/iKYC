from dotenv import load_dotenv
import os

load_dotenv()
redis_host = os.getenv('REDIS_HOST')
app_name = os.getenv('APP_NAME')

if redis_host and app_name:
    print("✅ .env file created and working!")
    print(f"Redis Host: {redis_host}")
    print(f"App Name: {app_name}")
else:
    print("❌ .env file not working")
