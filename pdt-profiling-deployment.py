# author: Eaton Wu

from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
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


def configure_deployment(incoming_time, querying_time, outgoing_time):
    pass


def process_data():
    pass


def output_data():
    pass


def get_list_kafka_topics(server='localhost:9092'):
    admin_client = KafkaAdminClient(bootstrap_servers=server)
    topic_list = admin_client.list_topics()
    admin_client.close()
    return topic_list


def connect_to_kafka_server(*topics, server='localhost:9092') -> KafkaConsumer:
    consumer = KafkaConsumer(topics, bootstrap_servers=server)
    pass


def configure_verbosity(verbosity: str):
    settings = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    if verbosity in settings:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=verbosity)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level='WARNING')
    logging.info("Logging configured")


def main():
    args = parse_args()
    configure_deployment(args.incoming, args.querying, args.outgoing)

    pass


if __name__ == '__main__':
    main()
