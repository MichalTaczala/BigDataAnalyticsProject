from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, FloatType, StringType, LongType
import logging
from kafka import KafkaProducer
import json

from inference import inference, get_data, get_features
from flight_data.models import FlightInfo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Spark session
spark = SparkSession.builder \
    .appName("KafkaFlightPrediction") \
    .getOrCreate()

# Kafka configurations
kafka_broker = "10.186.0.31:9092"
input_topic = "flightInfo"
output_topic = "predictionData"

input_schema = StructType([
    StructField("lastSeen", LongType(), True),
    StructField("arrivalAirport", StringType(), True),
    StructField("callsign", StringType(), True),
    StructField("icao24", StringType(), True),
    StructField("sessionID", StringType(), True),
])

# Read from Kafka
input_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", input_topic) \
    .option("startingOffsets", "earliest") \
    .load()

# Parse Kafka messages
parsed_stream = input_stream.selectExpr("CAST(value AS STRING) as value") \
    .select(from_json(col("value"), input_schema).alias("data")) \
    .select("data.*")

# Create Kafka producer
kafka_producer = KafkaProducer(
    bootstrap_servers=kafka_broker,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Apply inference function
def predict_batch(df, batch_id):
    try:
        logger.info("Processing batch %s", batch_id)

        # Convert DataFrame to list of rows
        rows = df.collect()

        # Create FlightInfo objects
        flights = [
            FlightInfo(
                row['icao24'],
                row['lastSeen'],
                row['arrivalAirport'],
                row['callsign']
            ) for row in rows if row['icao24'] is not None and row['lastSeen'] is not None and row['arrivalAirport'] is not None
        ]
        logger.info("Flight: %s", flights)
        if not flights:
            logger.info("No valid flights found in %s", rows)
            return

        data = get_data(flights)

        logger.info("Data: %s", data)

        X = get_features(data)

        logger.info("Features: %s", X)
        y_pred = list(map(float, inference(X)))
        logger.info("Predictions: %s", y_pred)

        for datapoint, y, row in zip(data, y_pred, rows):
            d = {
                key: value
                for key, value in zip(datapoint.get_attribute_names(), datapoint.get_values())
            }
            d["time_to_arrival"] = y
            d["sessionID"] = row["sessionID"]
            d["icao24"] = row["icao24"]
            kafka_producer.send(output_topic, value=d)

            logger.info("Sent prediction to Kafka: %s", d)

    except Exception as e:
        logger.error("Error during batch processing: %s", e)


# Write to Kafka
output_query = parsed_stream.writeStream \
    .foreachBatch(predict_batch) \
    .start()

# Wait for termination
output_query.awaitTermination()
