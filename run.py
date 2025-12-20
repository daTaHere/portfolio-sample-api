"""
Application entry point.
Instantiates the Flask app using the application factory pattern.
"""

from app import create_app
import os

# Create Flask application instance
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    # Run the development server
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "yes"]

    print(f"\n{'='*60}")
    print(f"🚀 Starting Flask Application")
    print(f"{'='*60}")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"{'='*60}\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
