# author: Eaton Wu
import time

import yaml
from confluent_kafka import Consumer, Producer, admin
from confluent_kafka.admin import AdminClient, NewTopic
import argparse
import psycopg2
import logging

DEFAULT_TIME = 0.5


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', metavar='VERBOSITY', help='Amount of info you want. Uses standard python logging levels,'
                                                        'going from DEBUG, INFO, WARNING, ERROR, and CRITICAL, where'
                                                        'WARNING is the default.', type=str, default='WARNING')
    parser.add_argument('--incoming', metavar='SECONDS', help='Amount of time to process incoming data',
                        default=DEFAULT_TIME)
    parser.add_argument('--querying', metavar='SECONDS', help='Amount of time to query the database',
                        default=DEFAULT_TIME)
    parser.add_argument('--outgoing', metavar='SECONDS', help='Amount of time to send out messages',
                        default=DEFAULT_TIME)

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


def configure_producer(outgoing_time):
    pass


def watch_topic(broker, read_topics: list, write_topic: str, incoming_time: float,
                querying_time: float, outgoing_time: float):
    """
    This function sets up the consumer. The consumer will subscribe to testing topic(s), query a database, and write
    to another topic
    :param broker:
    :param querying_time:
    :param outgoing_time:
    :param read_topics: a list of topics
    :param write_topic: the topic that's being written to
    :param incoming_time:
    :return:
    """
    topic_consumer = Consumer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               'group.id': 'development.kafka-ops.ko-api.consumer-test-eaton'
                               })

    topic_consumer.subscribe(read_topics)

    while True:
        returned_message = topic_consumer.poll(1)
        if returned_message is None:
            pass
        elif returned_message.error():  # is not a proper message
            logging.error('error: {}'.format(returned_message.error()))
        else:
            record_key = returned_message.key()
            record_value = returned_message.value()
            process_data(record_key, incoming_time)
            query_database(querying_time)
            output_data(broker, write_topic, record_key, record_value, outgoing_time)


def query_database(querying_time):
    time.sleep(querying_time)
    logging.info(f'Queried database for {querying_time}')


def process_data(record, incoming_time):
    time.sleep(incoming_time)
    logging.info(f'Processed record {record} for {incoming_time}')


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
    topic_producer = Producer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               })

    topic_producer.produce(write_topic, key=record_key, value=record_value, on_delivery=on_delivery_cb)
    topic_producer.poll(0)
    topic_producer.flush(1)
    pass


def get_list_kafka_topics(server='localhost:9092'):
    """
    Function that lists the topics of a broker.
    This function is mainly used to test the connectivity of a provided broker.
    :param server: the broker to list the topics from
    :return:
    """
    admin_client = AdminClient({'ssl.certificate.location': 'certs/ko-api.pem',
                                'ssl.key.location': 'certs/ko-api-key.pem',
                                'ssl.ca.location': 'certs/CARoot.pem',
                                'bootstrap.servers': server,
                                'security.protocol': 'ssl'
                                }, )
    topic_list = admin_client.list_topics(timeout=5)
    return topic_list.topics


def configure_verbosity(verbosity: str):
    settings = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    if verbosity in settings:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=verbosity)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level='WARNING')
    logging.info("Logging configured")


def get_config(filename: str):
    """
    Loads a configuration JSON file.
    A markdown file containing the possible key value pairs is in config_docs.md
    :param filename: the name of the configuraton file
    :return:
    """
    file = open(filename)
    config_dict = yaml.safe_load(file)
    return config_dict


def get_first_valid_broker(brokers: list) -> str:
    """
    Gets the first valid broker (a broker that has topics), given a list of brokers.
    This utilizes a function that makes use of the confluent_kafka.AdminClient class.
    :param brokers: a list of brokers
    :return: a string containing the first valid broker in a list, and an empty string if all brokers fail
    """
    for broker in brokers:
        topics = get_list_kafka_topics(broker)
        if len(topics) > 0:
            return broker

    return ''


def main():
    config_dict = get_config('config.yaml')
    parse_args()
    brokers = config_dict['brokers']
    broker = get_first_valid_broker(brokers)
    read_topic = config_dict['read_topic']
    write_topic = config_dict['write_topic']
    incoming_time = config_dict.get('incoming_time')
    querying_time = config_dict.get('querying_time')
    outgoing_time = config_dict.get('outgoing_time')

    watch_topic(broker, [read_topic],
                write_topic, incoming_time, querying_time, outgoing_time)


if __name__ == '__main__':
    main()
