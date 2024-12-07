# BigDataAnalyticsProject


to install opensky_api use pip install -e "git+https://github.com/openskynetwork/opensky-api.git#egg=opensky-api&subdirectory=python"


To run nifi, start it in GCP, run_nifi.sh then activate to see nifi flow: http://TUEXTERNALIDVM:9090/nifi/

To run jupyter notebook on spark-cluster:
jupyter notebook --no-browser --ip=0.0.0.0 --port=8888

http://EXTERNAL_VM_IP:8888/?token=<your_token>
