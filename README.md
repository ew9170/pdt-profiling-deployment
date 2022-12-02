# What does this do?

This application is meant to profile performance of a Kafka-Postgres pipeline.
It doesn't need to be run from within a cluster, but that may be necessary to
have access to your Postgres server.

## Quick Start

These certificates are used to connect to the brokers specified in the configuration file.

Create the secrets from the certificates (replace the --from-file argument):
caroot-pem will likely be called "CARoot.pem".

```bash
kubectl create secret generic caroot-pem --from-file='caroot_file_here'
```
cert-pem will likely be in the format "{service-account-name}.pem".
```bash
kubectl create secret generic cert-pem --from-file='cert_here'
```
privatekey-pem will likely be in the format "{service-account-name}-key.pem".
```bash
kubectl create secret generic privatekey-pem --from-file='key_here' 
```

Then, create the ConfigMap, which is then mounted onto the containers/pods:

```bash
kubectl create configmap config-file --from-file config.yaml
```

Deploy the deployment:

```bash
kubectl apply -f ./profiling-deployment.yaml
```

Get the pod names:

```bash
kubectl get pods -l app=profiling-deployment
```

Get output of the profiling pod:

Note that the output file will only exist if the program has
received a message from the kafka topic(s) that it's subscribed to.
The output file name can also be specified in the configuration file under the key
"output_settings.output_to_file"
```bash
kubectl exec {pod_name_here} -- "cat outputfile.txt"
```

Alternatively:

```bash
kubectl logs {pod_name_here}
```


## How does it work?

The application supports one command line argument, which allows you to
configure the output verbosity. The rest of the configurations lie in a file
that must be named config.yaml.

For more information about the verbosity settings, run:

```bash
python pdt-profiling-deployment.py -h
```

All this thing does is subscribe to some specified kafka topics,
sleep for some amount of time (specified in the config file) to emulate
processing, connect to a database with a query (also optionally sleeping
for some amount of time), and then writing the received message onto some
other specified topic for some specified amount of time (specified in the config file).

## Configuration

The program reads in settings for the program from a file called config.yaml.
For more information about the format of the configuration file, read config_README.md.

In order to pass in the configration file, you will need to create a ConfigMap from the config file
using the following command:

```bash
kubectl create configmap config-file --from-file config.yaml
```

## Secrets

In order to load your certificate authority, private key, and certificate pem files,
you may need to run the following commands:

It's important to note that the filenames of these secrets will be preserved when mounted
onto the container. (ie the --from-file argument will be preserved, and the caroot-pem/cert-pem/privatekey-pem
name is only used for specifying sources in the deployment YAML manifest.)

```bash
kubectl create secret generic caroot-pem --from-file='caroot_file_here'
kubectl create secret generic cert-pem --from-file='cert_here' 
kubectl create secret generic privatekey-pem --from-file='key_here' 
```

Inside the container, there will be a certs directory containing the secrets specified
using these commands.
