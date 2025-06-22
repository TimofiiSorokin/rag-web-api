#!/usr/bin/env python3
"""
Test script for chat endpoint
"""

import requests
import json
import sseclient

def test_chat_endpoint():
    """Test the chat endpoint with streaming response"""
    
    # Chat endpoint URL
    url = "http://localhost:8000/api/v1/chat/"
    
    # Test query
    payload = {
        "query": "What documents do we have? Please provide a brief overview of the files.",
        "max_results": 3
    }
    
    print("Testing chat endpoint...")
    print(f"Query: {payload['query']}")
    print("-" * 50)
    
    try:
        # Make streaming request
        response = requests.post(
            url,
            json=payload,
            headers={'Accept': 'text/event-stream'},
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Chat endpoint is working!")
            print("Streaming response:")
            print("-" * 30)
            
            # Parse SSE response
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.event == "message":
                    data = json.loads(event.data)
                    print(data.get('content', ''), end='', flush=True)
                elif event.event == "end":
                    print("\n" + "-" * 30)
                    print("✅ Stream completed successfully!")
                    break
                elif event.event == "error":
                    data = json.loads(event.data)
                    print(f"\n❌ Error: {data.get('content', '')}")
                    break
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_chat_health():
    """Test chat health endpoint"""
    
    url = "http://localhost:8000/api/v1/chat/health"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat health check:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check exception: {e}")

if __name__ == "__main__":
    print("Testing Chat API...")
    print("=" * 50)
    
    # Test health first
    test_chat_health()
    print()
    
    # Test chat endpoint
    test_chat_endpoint() 