from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import requests
import json

app = FastAPI()

# Asterisk REST Interface configuration (adjust these)
ASTERISK_HOST = "pbx.articence.com"  # IP or hostname of your Asterisk server
ASTERISK_PORT = 8089  # Default Asterisk REST port
ASTERISK_USERNAME = "articencevoc"
ASTERISK_PASSWORD = "546243676f6c5304fd97f82e21f7ba12"

# Function to authenticate with Asterisk REST API
def get_asterisk_auth():
    return (ASTERISK_USERNAME, ASTERISK_PASSWORD)

# Function to make requests to the Asterisk REST API
def make_asterisk_request(endpoint, params=None, method="GET"):
    url = f"http://{ASTERISK_HOST}:{ASTERISK_PORT}/ari/{endpoint}"
    try:
      if method == "GET":
        response = requests.get(url, auth=get_asterisk_auth(), params=params, verify=False) #verify=False only in dev/test, use certificates in production
      elif method == "POST":
        response = requests.post(url, auth=get_asterisk_auth(), json=params, verify=False) #verify=False only in dev/test, use certificates in production
      else:
        raise HTTPException(status_code=405, detail="Method Not Allowed")

      response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
      return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Asterisk: {e}")
        raise HTTPException(status_code=500, detail=f"Asterisk Error: {e}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response from Asterisk: {e}")
        raise HTTPException(status_code=500, detail="Invalid JSON from Asterisk")
    
# Make a call
@app.post("/call")
async def make_call(caller: str, callee: str):  # Use query parameters or request body
    try:
        endpoint = "channels"
        params = {
            "endpoint": f"SIP/{caller}",  # Example: SIP/1001
            "extension": callee,  # Example: 2001
            "context": "from-internal", #Example: from-internal
            "priority": 1
        }
        response = make_asterisk_request(endpoint, params, "POST")
        return JSONResponse(content={"message": "Call initiated", "channel_id": response["id"]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error making call: {e}")


# Transfer a call (requires the channel ID)
@app.post("/transfer/{channel_id}")
async def transfer_call(channel_id: str, destination: str):
  try:
      endpoint = f"channels/{channel_id}/redirect"
      params = {
          "endpoint": f"SIP/{destination}"  # Example: SIP/1002
      }
      make_asterisk_request(endpoint, params, "POST")
      return JSONResponse(content={"message": "Call transferred"})
  except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error transferring call: {e}")


# Hold a call (requires the channel ID)
@app.post("/hold/{channel_id}")
async def hold_call(channel_id: str):
    try:
        endpoint = f"channels/{channel_id}/hold"
        make_asterisk_request(endpoint, method="POST")
        return JSONResponse(content={"message": "Call placed on hold"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error holding call: {e}")

# Unhold a call (requires the channel ID)
@app.post("/unhold/{channel_id}")
async def unhold_call(channel_id: str):
    try:
        endpoint = f"channels/{channel_id}/unhold"
        make_asterisk_request(endpoint, method="POST")
        return JSONResponse(content={"message": "Call unheld"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unholding call: {e}")


# Hangup a call (requires the channel ID)
@app.delete("/hangup/{channel_id}")
async def hangup_call(channel_id: str):
    try:
        endpoint = f"channels/{channel_id}"
        make_asterisk_request(endpoint, method="DELETE")
        return JSONResponse(content={"message": "Call hung up"})
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error hanging up call: {e}")



# Get channel information (example)
@app.get("/channels/{channel_id}")
async def get_channel_info(channel_id: str):
    try:
        endpoint = f"channels/{channel_id}"
        response = make_asterisk_request(endpoint)
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting channel info: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)