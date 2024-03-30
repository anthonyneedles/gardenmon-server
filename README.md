# GardenMon Server

The GardenMon Server is meant to serve out data from the database that holds environmental data reported by the GardenMon devices (see [gardenmon](https://github.com/anthonyneedles/gardenmon)).

## Setup

1. Clone the repo and run the init script.

```
git clone https://github.com/anthonyneedles/gardenmon-server.git
cd gardenmon-server
./init.sh
```

2. Fill in `local_options.py`.
For security reasons, this file does not get tracked by git.

3. Start the GardenMon Server service with:

```
sudo systemctl start gardenmon_server
```

## Useful Commands

To start/stop/restart the service:

```
sudo systemctl start gardenmon
sudo systemctl stop gardenmon
sudo systemctl restart gardenmon
```

To observe the status of the service:

```
systemctl status gardenmon
```

To read the stdout of the service:

```
journalctl -eu gardenmon
```

To test that the server is running:

```
curl localhost:5000/test
```

