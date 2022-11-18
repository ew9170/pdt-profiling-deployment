import string

from confluent_kafka import Producer
import random
"""
Author: Eaton Wu

This is a little CLI tool that allows users to produce messages into a specified topic.
"""

delivered_records = 0


def on_delivery_cb(err, msg):
    global delivered_records
    """Delivery report handler called on
    successful or failed delivery of message
    """
    if err is not None:
        print("Failed to deliver message: {}".format(err))
    else:
        delivered_records += 1
        print("Produced record to topic {} partition [{}] @ offset {}"
              .format(msg.topic(), msg.partition(), msg.offset()))


def write_message(broker, write_topic):
    topic_producer = Producer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               })
    user_key = input('key: ')
    user_value = input('value: ')
    topic_producer.produce(write_topic, key=user_key, value=user_value, on_delivery=on_delivery_cb)
    topic_producer.poll(0)
    topic_producer.flush(5)


def write_random_messages(broker, write_topic):
    topic_producer = Producer({'ssl.certificate.location': 'certs/ko-api.pem',
                               'ssl.key.location': 'certs/ko-api-key.pem',
                               'ssl.ca.location': 'certs/CARoot.pem',
                               'bootstrap.servers': broker,
                               'security.protocol': 'ssl',
                               })
    quantity = int(input('quantity of messages: '))
    message_size = int(input('size of messages (in chars): '))
    for i in range(quantity):
        out_key = ''.join(random.choices(string.ascii_lowercase, k=message_size))
        out_value = ''.join(random.choices(string.ascii_lowercase, k=message_size))
        topic_producer.produce(write_topic, key=out_key, value=out_value, on_delivery=on_delivery_cb)

    topic_producer.poll(0)
    topic_producer.flush(5)

def menu():
    user_input = -1
    brokers = [
        'secured-kafka01.dlas1.ucloud.int:9093',
        'secured-kafka02.dlas1.ucloud.int:9093',
        'secured-kafka03.dlas1.ucloud.int:9093',
        'secured-kafka04.dlas1.ucloud.int:9093',
        'secured-kafka05.dlas1.ucloud.int:9093',
    ]
    while user_input != 0:
        user_input = int(input("0.) Exit\n1.) Write a message to the topic\n"
                               "2.) Write random messages to the topic\n"))
        function_map = {1: write_message, 2: write_random_messages}
        if user_input == 0:
            exit(0)
        if user_input in function_map:
            function_map[user_input](brokers[0], 'development.internal.kafka-ops.read-test-eaton')
        else:
            print('Invalid command')


def main():
    menu()


if __name__ == '__main__':
    main()
