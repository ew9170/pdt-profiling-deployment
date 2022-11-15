# author: Eaton Wu

from kafka import KafkaConsumer, KafkaProducer
import argparse
import psycopg2

DEFAULT_TIME = 0.5

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--incoming', metavar='SECONDS', help='Amount of time to process incoming data',
                        default=DEFAULT_TIME)
    parser.add_argument('--querying', metavar='SECONDS', help='Amount of time to query the database',
                        default=DEFAULT_TIME)
    parser.add_argument('--outgoing', metavar='SECONDS', help='Amount of time to send out messages',
                        default=DEFAULT_TIME)
    return parser.parse_args()


def configure_deployment(args):
    pass


def process_data():
    pass


def main():
    args = parse_args()
    configure_deployment(args)
    pass


if __name__ == '__main__':
    main()
