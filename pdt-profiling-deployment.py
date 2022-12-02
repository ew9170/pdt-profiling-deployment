# author: Eaton Wu
import confluent_kafka
import yaml
from confluent_kafka import Consumer, Producer, admin
from confluent_kafka.admin import AdminClient, NewTopic
import argparse
import psycopg2
import logging
import time
import threading

import postgres_queries

DEFAULT_TIME = 0
ui_mode = False

total_kafka_read_time = 0
total_kafka_write_time = 0
total_db_query_time = 0
most_recent_record = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', metavar='VERBOSITY', help='Amount of info you want. Uses standard python logging levels,'
                                                        ' going from DEBUG, INFO, WARNING, ERROR, and CRITICAL, where'
                                                        ' WARNING is the default.', type=str, default='WARNING')

    args = parser.parse_args()
    configure_verbosity(args.v)

    if args.incoming is not None:
        if args.incoming < 0:
            logging.error('incoming must be > 0 seconds')
            exit(-1)

    if args.querying is not None:
        if args.querying < 0:
            logging.error('querying must be > 0 seconds')
            exit(-1)

    if args.outgoing is not None:
        if args.outgoing < 0:
            logging.error('outgoing must be > 0 seconds')
            exit(-1)

    return args


def log_new_times(kafka_read, kafka_write, db_query):
    global total_db_query_time
    global total_kafka_read_time
    global total_kafka_write_time

    total_db_query_time = total_db_query_time + db_query
    total_kafka_read_time = total_kafka_read_time + kafka_read
    total_kafka_write_time = total_kafka_write_time + kafka_write

    logging.info(f" --- Total time updated ---\n"
                 f"Total Read Time: {total_kafka_read_time}\n"
                 f"Total Write Time: {total_kafka_write_time}\n"
                 f"Total Query Time: {total_db_query_time}")


def print_total_times():
    global total_db_query_time
    global total_kafka_read_time
    global total_kafka_write_time

    logging.info(f" --- Total time ---\n"
                 f"Total Read Time: {total_kafka_read_time}\n"
                 f"Total Write Time: {total_kafka_write_time}\n"
                 f"Total Query Time: {total_db_query_time}\n")


def watch_topic(config_dict: dict):
    """
    This function sets up the consumer. The consumer will subscribe to testing topic(s), query a database, and write
    to another topic
    :param config_dict:
    :return:
    """
    global total_kafka_read_time
    global total_kafka_write_time
    global total_db_query_time
    global most_recent_record

    # the broker and these three settings must be specified in config.yaml

    brokers = config_dict['brokers']
    certs = config_dict['certs']
    broker = None

    try:
        broker = get_first_valid_broker(certs, brokers)
    except Exception as e:
        logging.error(e)
        exit(-1)
    read_topics = config_dict['read_topics']
    write_topic = config_dict['write_topic']

    # these settings are optional
    incoming_time = config_dict.get('incoming_time', 0)
    querying_time = config_dict.get('querying_time', 0)
    outgoing_time = config_dict.get('outgoing_time', 0)
    postgres_settings = config_dict.get('postgres')
    output_settings = config_dict.get('output_settings')
    output_to_file = output_settings.get('output_to_file', 'output.txt')

    topic_consumer = Consumer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               'group.id': 'development.kafka-ops.ko-api.consumer-test-eaton'
                               })

    if read_topics is None or write_topic is None:
        logging.error('read_topics and write_topic must be specified')
        raise Exception('read_topics and write_topic cannot be None')

    topic_consumer.subscribe(read_topics)
    is_first_message = True
    time_first_message = time.time()

    while True:
        returned_message = topic_consumer.poll(5)
        if returned_message is None:
            pass
        elif returned_message.error():  # is not a proper message
            logging.error('error: {}'.format(returned_message.error()))
        else:
            time_start = time.time()
            if is_first_message:
                is_first_message = False
                time_first_message_end = time.time()
                logging.info("Time to first message: {time_first_message} seconds"
                             .format(time_first_message=str(time_first_message_end - time_first_message)))
            most_recent_record = returned_message
            record_key = returned_message.key().decode()
            record_value = returned_message.value().decode()
            kafka_read_time = process_data(returned_message, incoming_time, time_start)
            db_query_time = query_database(querying_time, postgres_settings)
            kafka_write_time = output_data(broker, write_topic, record_key, record_value, outgoing_time)
            log_new_times(kafka_read_time, kafka_write_time, db_query_time)

            if output_to_file is not None:
                parseable_output = {"record_key": record_key, "kafka_read_time": kafka_read_time,
                                    "kafka_write_time": kafka_write_time, "db_query_time": db_query_time,
                                    "total_read_time": total_kafka_read_time, "total_write_time": total_kafka_write_time,
                                    "total_db_query_time": total_db_query_time}
                file = open(output_to_file, 'a+')
                with file:
                    file.write(str(parseable_output) + '\n')


def query_database(querying_time, postgres: dict = None):
    """
    something about stored procedures?

    :param postgres: dict potentially containing: { host, port, username, password, dbname }
    :param querying_time:
    :return:
    """
    time_start = time.time()

    if postgres is not None:
        dbname = postgres.get('dbname')
        user = postgres.get('user')
        password = postgres.get('password')
        host = postgres.get('host')
        port = postgres.get('port')
        min_range = postgres.get('min_range')
        max_range = postgres.get('max_range')
        try:
            connection = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            with connection:
                table_name = postgres_queries.get_random_table(connection)
                postgres_queries.select_random_rows_from_table(connection, table_name, min_range, max_range)
            connection.close()
        except psycopg2.OperationalError as e:
            logging.error(e)
            time_end = time.time()
            time_elapsed = time_end - time_start
            logging.info(f'Query failed in {time_elapsed} seconds')
            return time_elapsed

    else:
        time.sleep(querying_time)
    time_end = time.time()
    time_elapsed = time_end - time_start
    logging.info(f'Queried database in {time_elapsed} seconds')
    return time_elapsed


def process_data(message, incoming_time, time_start):
    time.sleep(incoming_time)
    time_end = time.time()
    time_elapsed = time_end - time_start
    logging.info(f'Processed record \'{message.key().decode()}\' in {time_elapsed} seconds')
    return time_elapsed


def on_delivery_cb(err, msg):
    """Delivery report handler called on
    successful or failed delivery of message
    """
    if err is not None:
        logging.error("Failed to deliver message: {}".format(err))
    else:
        logging.info("Produced record to topic {} partition [{}] @ offset {}"
                     .format(msg.topic(), msg.partition(), msg.offset()))


def output_data(broker, write_topic, record_key, record_value, outgoing_time):
    time_start = time.time()
    topic_producer = Producer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               })

    topic_producer.produce(write_topic, key=record_key, value=record_value, on_delivery=on_delivery_cb)
    topic_producer.poll(0)
    topic_producer.flush(1)
    time.sleep(outgoing_time)
    time_end = time.time()
    time_elapsed = time_end - time_start

    logging.info('Produced record {record_key} in {time_elapsed} seconds'.format(record_key=record_key,
                                                                                 time_elapsed=time_elapsed))
    return time_elapsed


def get_list_kafka_topics(certs: dict, server='localhost:9092'):
    """
    Function that lists the topics of a broker.
    This function is mainly used to test the connectivity of a provided broker.
    :param certs: dict containing (CA, private_key, certificate)
    :param server: the broker to list the topics from
    :return:
    """

    if certs is None:
        logging.error("certs not specified in configuration")
        exit(-1)

    if certs.get('CA') is None or certs.get('private_key') is None or certs.get('certificate') is None:
        logging.error("certs configuration must contain CA, private_key and certificate")
        exit(-1)

    admin_client = AdminClient({'ssl.certificate.location': certs.get('certificate'),
                                'ssl.key.location': certs.get('private_key'),
                                'ssl.ca.location': certs.get('CA'),
                                'bootstrap.servers': server,
                                'security.protocol': 'ssl'
                                }, )
    try:
        topic_list = admin_client.list_topics(timeout=5)
        return topic_list.topics
    except confluent_kafka.KafkaException:
        return


def configure_verbosity(verbosity: str):
    settings = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    if verbosity in settings:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=verbosity)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level='WARNING')
    logging.info("Logging configured")


def get_config(filename: str):
    """
    Loads a configuration YAML file.
    A markdown file containing the possible key value pairs is in README.md
    :param filename: the name of the configuration file
    :return:
    """
    file = open(filename)
    config_dict = yaml.safe_load(file)
    return config_dict


def get_first_valid_broker(certs: dict, brokers: list) -> str:
    """
    Gets the first valid broker (a broker that has topics), given a list of brokers.
    This utilizes a function that makes use of the confluent_kafka.AdminClient class.
    :param certs: CA, private key, and certificate passed in via the config file
    :param brokers: a list of brokers
    :return: a string containing the first valid broker in a list, and an empty string if all brokers fail
    """
    for broker in brokers:
        topics = get_list_kafka_topics(certs, broker)
        if topics is not None and len(topics) > 0:
            logging.info('Connected to broker {}'.format(broker))
            return broker

    raise Exception('No valid broker found')


def main():
    parse_args()
    try:
        config_dict = get_config('config/config.yaml')
        watch_topic(config_dict)
    except FileNotFoundError:
        logging.error("Configuration file not found")


if __name__ == '__main__':
    main()
