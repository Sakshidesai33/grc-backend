import requests
import subprocess
import time

# Start server in background
process = subprocess.Popen(['python', '-m', 'uvicorn', 'app_new.main:app', '--reload', '--port', '8000', '--host', '0.0.0.0'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)

# Wait for server to start
time.sleep(5)

try:
    print('=== SIMPLE AUTH TEST ===')
    
    # Test basic server
    response = requests.get('http://localhost:8000/', timeout=5)
    print(f'Server Status: {response.status_code}')
    
    # Test OpenAPI docs
    response = requests.get('http://localhost:8000/docs', timeout=5)
    print(f'Docs Status: {response.status_code}')
    
    # Test registration endpoint exists
    response = requests.post('http://localhost:8000/api/auth/register', json={}, timeout=5)
    print(f'Registration endpoint Status: {response.status_code}')
    print(f'Registration Response: {response.text[:300]}')
    
except Exception as e:
    print(f'Error: {str(e)}')

# Clean up
process.terminate()
