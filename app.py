from app import create_app

# Instantiate the Flask Application
app = create_app()

if __name__ == '__main__':
    # Launch local development server
    app.run(debug=True, host='0.0.0.0', port=5000)
