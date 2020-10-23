# Note: this set up in UNtested - there are probably more steps required

# SET UP S3 PRIVILEGES

sudo apt update
sudo apt install -y awscli python3 python3-pip

sudo ln -s /usr/bin/python3 /usr/bin/python
sudo ln -s /usr/bin/pip3 /usr/bin/pip

git clone git@github.com:lukerm/parkrun-map
pip install parkrun-map/

# Sync athletes table
aws s3 sync s3://lukerm-ds-open/parkrun/data/parquet/athletes /home/ubuntu/parkrun-map/data/athletes/
# Add this line to crontab (without comment marker)
# 0 * * * * /usr/bin/aws s3 sync s3://lukerm-ds-open/parkrun/data/parquet/athletes /home/ubuntu/parkrun-map/data/athletes/

# Create a tmux session for this or prefix with nohup
PORT=2070
waitress-serve --port=$PORT parkrun_map.map_app:map_app.server

# For rerouting port 80 (HTTP default) to e.g. 8080 or 2070, see the following guide:
# https://serverfault.com/questions/112795/how-to-run-a-server-on-port-80-as-a-normal-user-on-linux
