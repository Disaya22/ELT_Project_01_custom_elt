import subprocess  # this is how we're allowing to control inputs and outputs and things like that
import time

# the next thing we'll do is 'double check' (the docker compose file check) to make sure
# that the elt script will not run unless the source and destination database are working
# but we can also run a fallback 
def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    """รอจนกว่า PostgreSQL จะพร้อมใช้งาน Wait for PostgreSQL to become available."""
    retries = 0
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", host], check=True, capture_output=True, text=True)
            if "accepting connections" in result.stdout:
                print("เชื่อมต่อกับ PostgreSQL เสร็จสมบูรณ์! Successfully connected to PostgreSQL!")
                return True
        except subprocess.CalledProcessError as e:
            print(f"ไม่สามารถเชื่อมต่อกับ PostgreSQL Error connecting to PostgreSQL: {e}")
            retries += 1
            print(
                f"Retrying in {delay_seconds} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(delay_seconds)
    print("Max retries reached. Exiting.")
    return False


# Use the function before running the ELT process
if not wait_for_postgres(host="source_postgres"):
    exit(1)

print("เริ่มกระบวนการ ELT... Starting ELT script...")

# Configuration for the source PostgreSQL database
source_config = {
    'dbname': 'source_db', # define name of source database
    'user': 'postgres',
    'password': 'secret',
    # Use the service name from docker-compose as the hostname
    'host': 'source_postgres'
}

# Configuration for the destination PostgreSQL database
destination_config = {
    'dbname': 'destination_db', # define name of destination database
    'user': 'postgres',
    'password': 'secret',
    # Use the service name from docker-compose as the hostname
    'host': 'destination_postgres'
}


# We need to create dump command for initializing the source data 
# Use pg_dump to dump the source database to a SQL file
dump_command = [
    'pg_dump',
    '-h', source_config['host'],
    '-U', source_config['user'],
    '-d', source_config['dbname'],
    '-f', 'data_dump.sql', # f is going to be the file we'll use
    '-w'  # Do not prompt for password
]

# We'll set the environment variable to avoid the password dump
# Set the PGPASSWORD environment variable to avoid password prompt
subprocess_env = dict(PGPASSWORD=source_config['password'])
# Now we've created a PGpassword environment variable that will 
# not ask us for the password every single time

# Next, we'll execute dump_command
# Execute the dump command
# env=subprocess_env => point the command below the environment variable that we just created
# So, this command'll dump everthing into the source db
subprocess.run(dump_command, env=subprocess_env, check=True)

# But our work is to get everything from the source db over to the destination db

# We're going to create a load command
# Use psql to load the dumped SQL file into the destination database
load_command = [
    'psql',
    '-h', destination_config['host'],
    '-U', destination_config['user'],
    '-d', destination_config['dbname'],
    '-a', '-f', 'data_dump.sql'
]

# Set the PGPASSWORD environment variable for the destination database
subprocess_env = dict(PGPASSWORD=destination_config['password'])


# Execute the load command
subprocess.run(load_command, env=subprocess_env, check=True)

print("Ending ELT script...")

# now this'll be our full on elt script

#Next, we'll use docker to completely run this