import requests
from django.conf import settings
import json

def get_usage_prediction(house_id):
    """
    Fetch usage prediction data from the prediction API
    """
    try:
        url = f"https://saroshirfan27.pythonanywhere.com/predict/?format=json&house_id={house_id}"
        print(f"Making request to: {url}")
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response content: {response.text}")
        
        if response.status_code != 200:
            print(f"API returned error status: {response.status_code}")
            return {
                "house_id": str(house_id),
                "predicted_usage": 0.0,
                "error": f"API returned status code {response.status_code}"
            }
            
        try:
            data = response.json()
            print(f"Successfully parsed JSON data: {data}")
            
            if not data or "prediction_kWh" not in data:
                return {
                    "house_id": str(house_id),
                    "predicted_usage": 0.0,
                    "error": "Invalid response format from API"
                }
            
            return {
                "house_id": str(data.get("house_id", house_id)),
                "predicted_usage": float(data.get("prediction_kWh", 0.0))
            }
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
            print(f"Raw response: {response.text}")
            return {
                "house_id": str(house_id),
                "predicted_usage": 0.0,
                "error": "Failed to parse API response"
            }
            
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return {
            "house_id": str(house_id),
            "predicted_usage": 0.0,
            "error": f"Failed to connect to prediction API: {str(e)}"
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            "house_id": str(house_id),
            "predicted_usage": 0.0,
            "error": f"Unexpected error: {str(e)}"
        } 