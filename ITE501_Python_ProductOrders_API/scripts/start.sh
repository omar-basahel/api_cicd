#!/bin/bash
cd /home/ec2-user/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

PORT=5000
API_KEY=changeme-ite501
DATA_FILE=./data/db.json
BEARER_TOKEN=my-static-bearer-token
BASIC_USER=test
BASIC_PASS=pass

nohup python3 app.py &
