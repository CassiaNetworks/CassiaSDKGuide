import time
from sse_data_thread import SSEDataThread

"""
SSE Stream Handler for Scanned Advertisement Data Packets using AC Managed Mode.

This is an example program to collect SSE scanned advertisement data from the AC API 
and process the adData from the packet JSON.
"""

def start(stream_thread, url, output_file):
    """Starts streaming and processing scores data."""
    stream_thread = SSEDataThread(url, output_file)
    stream_thread.daemon = True
    stream_thread.start()
    return stream_thread


def stop(stream_thread):
    """Stops streaming and processing scores data."""
    if stream_thread and stream_thread.is_alive():
        stream_thread.stop() # Set internal event flag to True to kill thread.
        stream_thread.join() # Make sure thread finishes before continuing with main thread.


def main():
    stream_thread = None
    access_token = "abcdefghijklmnopqrstuvwxyz"
    mac_address = "CC:1B:E0:E0:12:AB"
    ac_address = "http://demo.cassia.pro"
    url = ac_address + "/api/gap/nodes?event=1&mac=" + mac_address + "&access_token=" + access_token
    output_file = open("example_output.txt", "a")
    stream_thread = start(url, output_file)
    print("Collecting and processing packet data for 10 seconds.")
    time.sleep(10)
    stop(stream_thread)


if __name__ == "__main__":
    main()