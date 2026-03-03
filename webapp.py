from flask import Flask, render_template, jsonify
import subprocess
import json
import os


app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run-crawler', methods=['POST'])
def run_crawler():
    output_file = 'crawler_results.json'
    
    try:
        result = subprocess.run(
            [ 'python3', '-m', 'scrapy', 'runspider', 'crawler/webcrawler/webcrawler/spiders/website_crawler.py', '-o', output_file,],
            

            capture_output=True, text=True, check=True, timeout=600
        )

        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                file_content= f.read().strip()
                if not file_content:
                    data = []
                else:
                    

                    try:
                        data =json.loads(file_content)
                    except json.JSONDecodeError:

                        f.seek(0)
                        data= []
                        for line in f:
                            if line.strip():
                                data.append(json.loads(line))
                return jsonify({
                    'status': 'success',
                    'data': data,
                    'message': f'Found {len(data)} items'
                })

        else:
            return jsonify({
                'status': 'error',
                'message': 'No results file created'
            })

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'Error',
            'message': 'Crawler Timed Out'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'Error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)