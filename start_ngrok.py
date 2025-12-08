from pyngrok import ngrok
import time
import sys
import os

def main():
    # Allow the user to provide an ngrok authtoken via env var
    token = os.environ.get("NGROK_AUTH_TOKEN") or os.environ.get("NGROK_AUTHTOKEN") or os.environ.get("NGROK_TOKEN")
    if not token:
        print("NGROK_MISSING_TOKEN: set NGROK_AUTH_TOKEN env var with your ngrok authtoken")
        sys.stdout.flush()
        sys.exit(2)

    try:
        ngrok.set_auth_token(token)
    except Exception:
        # proceed; pyngrok may still work if ngrok binary is configured
        pass

    # Start an HTTP tunnel to port 5000
    tunnel = ngrok.connect(5000, "http")
    print("NGROK_URL=" + tunnel.public_url)
    sys.stdout.flush()
    try:
        # Keep the script running so the tunnel stays alive
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        try:
            ngrok.disconnect(tunnel.public_url)
        except Exception:
            pass
        ngrok.kill()

if __name__ == '__main__':
    main()
