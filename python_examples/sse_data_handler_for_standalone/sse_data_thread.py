import threading
import requests
import sseclient
import json

"""
This example uses the sseclient library to handle SSE streams.
You may want to put this in a separate thread or process so it doesn't block.
"""

class SSEDataThread(threading.Thread):

    def __init__(self, url, f):
        threading.Thread.__init__(self, target=self._stream_threader)
        self._kill = threading.Event()
        self._url = url
        self._outfile = f

    def _is_json(self, myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    def _stream_and_collect_packet_addata(self, sse_client_events):
        """
        Streams and collects packet adData from the SSE stream sse_client_events.
        :param sse_client_events: SSEClient iterator for SSE events.
        """
        for json_event in sse_client_events:
            if self._kill.is_set():
                break
            data_str = json_event.data.strip()
            if data_str != "" and self._is_json(data_str):
                event_json = json.loads(json_event.data)
                print(event_json)
                self._outfile.write(event_json["adData"] + "\n")

    def _stream_threader(self):
        """Function to run on each new SSEDataThread."""
        client_events = sseclient.SSEClient(self._url)
        self._stream_and_collect_packet_addata(client_events)

    def stop(self):
        """Stops SSEDataThread by setting kill Event flag."""
        if not self._kill.is_set():
            self._kill.set()
        self._outfile.close()

