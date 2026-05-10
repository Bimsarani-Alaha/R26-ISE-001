import subprocess
import sys
import os

def main():
    print("=" * 50)
    print("Starting ColorBlind Vision Backend")
    print("=" * 50)
    
    # Check if models exist
    if not os.path.exists("models/tshirt_color_classifier.h5"):
        print("ERROR: Model file not found at models/tshirt_color_classifier.h5")
        print("Please place your model files in the 'models' folder")
        sys.exit(1)
    
    if not os.path.exists("models/cvd_generator.keras"):
        print("ERROR: Model file not found at models/cvd_generator.keras")
        print("Please place your model files in the 'models' folder")
        sys.exit(1)
    
    print("✓ Models found")
    print("Starting server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    subprocess.run([sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    main()