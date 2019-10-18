import time
from sse_data_thread import SSEDataThread

def start(stream_thread, url, output_file):
    """Starts streaming and processing scores data."""
    stream_thread = SSEDataThread(url, output_file)
    stream_thread.daemon = True
    stream_thread.start()


def stop(stream_thread):
    """Stops streaming and processing scores data."""
    if stream_thread and stream_thread.isAlive():
        stream_thread.stop() # Set internal event flag to True to kill thread.
        stream_thread.join() # Make sure thread finishes before continuing with main thread.


def main():
    stream_thread = None
    access_token = "2e91e2e44910ff1005a3aa99554ccf618c15e091e03e66cd5c6122bbda12bb01"
    mac_address = "CC:1B:E0:E0:90:B4"
    url = "http://demo.cassia.pro/api/gap/nodes?event=1&mac=" + mac_address + "&access_token=" + access_token
    output_file = open("example_output.txt", "a")
    start(stream_thread, url, output_file)
    print("Collecting and processing packet data for 10 seconds.")
    time.sleep(30)
    stop(stream_thread)


if __name__ == "__main__":
    main()