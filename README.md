# BigDataAnalyticsProject


to install opensky_api use pip install -e "git+https://github.com/openskynetwork/opensky-api.git#egg=opensky-api&subdirectory=python"


To run nifi, start it in GCP, run_nifi.sh then activate to see nifi flow: http://TUEXTERNALIDVM:9090/nifi/

To run jupyter notebook on spark-cluster:
jupyter notebook --no-browser --ip=0.0.0.0 --port=8888

http://EXTERNAL_VM_IP:8888/?token=<your_token>




How to run Frontend:
cd front/
source app3/bin/activate
gunicorn --bind 0.0.0.0:8080 app:app

Żeby odpalić stronę na przeglądarce: http://34.116.172.181:8080/



Spark section:
export PYSPARK_PYTHON=./BigDataAnalyticsProject/venv/bin/python3.10
export PYSPARK_DRIVER_PYTHON=./BigDataAnalyticsProject/venv/bin/python3.10


Spark Streaming Run:
/opt/spark/bin/spark-submit     --master spark://10.186.0.32:7077  --py-files /home/michtaczala/BigDataAnalyticsProject/src/project.zip   --packages org.apache.spark:spark-sql-kafka-0-
10_2.12:3.5.1 /home/michtaczala/BigDataAnalyticsProject/src/pyspark/predict.py
