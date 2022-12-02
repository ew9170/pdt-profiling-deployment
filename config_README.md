# Config Specifications

This readme specifies possible configurations that you can use in
the config.yaml file. There will also be an example config that can start you off.

## Required

There are four fields that must be specified for the application to run
at all:

### brokers

This field is a list of Kafka brokers. It should be specified on the root level.

Example:
```yaml
"brokers":
  - "broker1.internal:1234"
  - "broker2.internal:1234"
```

### certs

This field specifies the file names of your certificate authority/certificate/private key.
As mentioned in the README, these files should also be added as secrets.
The profiling-deployment.yaml manifest will mount the secrets onto the pod(s).

If you don't have these files, you might want to post a message on the #kafka-ops-support Slack channel.

Example:
```yaml
"certs":
  "CA": "certs/CARoot.pem"
  "private_key": "certs/{service account}-key.pem"
  "certificate": "certs/{service-account}.pem"
  ```

### read-topics and write-topic
These are kind of self-explanatory:
The read-topics field specifies a list of topics that the
program will subscribe to and read from.

The write-topic field specifies a single topic to write to.

Example:

```yaml
"read_topics":
  - "development.internal.kafka-ops.read-example-1"
  - "development.internal.kafka-ops.read-example-2"
"write_topic": "development.internal.kafka-ops.write-example"
```

## Optional 

### incoming_time/outgoing_time/querying_time

These fields allow you to configure how long (at minimum) each step takes to complete.
This can be used to emulate some kind of processing.

By default, (if these fields are not specified), the values are set to 0.

Example:

```yaml
"incoming_time": 1
"querying_time": 0
"outgoing_time": 0
```

### output_settings.output_to_file

This field allows you to specify the filename you want the program
to output to. The reason that this is a nested field is that there were
previously multiple output settings, but I opted to remove them. 

By default, the output filename value is "output.txt".

Example:

```yaml
"output_settings":
  "output_to_file": "output.txt"
```

### postgres

This field allows you to configure your Postgres server information.
The min_range and max_range fields are optional; to emulate a
database query on a database we don't have any information of, I opted to
get choose a random table from the "information_schema.tables" table, and
to choose a random number of entries in the range [min_range, max_range].

Example:

```yaml
postgres:
  host: "localhost"
  port: 5432
  user: "admin"
  password: "admin"
  dbname: "postgresdb"
  min_range: 1  # optional
  max_range: 20  # optional
```





