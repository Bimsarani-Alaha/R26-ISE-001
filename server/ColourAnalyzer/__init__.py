# Makes ColourAnalyzer a proper Python package so `from ColourAnalyzer.app import app`
# works reliably from server.py, regardless of how the project is launched
# (python server.py, uvicorn server:app, packaged into an exe, etc).