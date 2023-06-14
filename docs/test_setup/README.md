# Setup for playing around

If you want to setup an instance yourself to develop or simply play around with the API,
you have to follow a couple of steps to set everything up.

## Install the necessary software

Make sure, that you've installed the necessary packages by running
```bash
pip install -r requirements.txt
```

in the project root.

## MongoDB setup

### Local installation

If you want to host the test database on your local machine, follow the install instructions
on the official mongoDB website. Make sure, either the service is running or you've executed the binary
afterwards. Otherwise, the motor client cant connect to the database.

If not done yet, create a .env file in the project root and put a line with the following content:
```
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
```

This is the default connection string for a local installation. Of course, if you've set a password
or run the service on a different port, this has to be adjusted.

## Atlas

If you're using a cluster installation of mongoDB, simply put lines like these in your .env file:
```
user=your_atlas_username
password=your_password
cluster=your_cluster_connection_string
MONGODB_CONNECTION_STRING=mongodb+srv://${user}:${password}@${cluster}.mongodb.net/test
```

# Fill the database with some values from OSM

To fill your database with some locations, execute the `load_sample_data.py` like this:
```bash
python load_sample_data.py
```

This will populate your DB with some values from Berlin.
