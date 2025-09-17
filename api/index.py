from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        "message": "Hello from Vercel!",
        "status": "success"
    })

@app.route('/test')
def test():
    return jsonify({
        "message": "Test endpoint working", 
        "status": "success"
    })

# Vercel WSGI适配器
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)