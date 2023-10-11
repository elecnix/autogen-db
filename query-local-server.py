from autogen import AssistantAgent, UserProxyAgent, config_list_from_models
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import threading
import requests

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'HELLO')

def run_server(started_event):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print('HTTP server is starting up...')
    started_event.set()  # Signal that the server is ready to handle requests
    httpd.serve_forever()

# Start server in a new thread
server_started_event = threading.Event()
server_thread = threading.Thread(target=run_server, args=(server_started_event,))
server_thread.start()
server_started_event.wait()

# Configure AutoGen
config_list = config_list_from_models(
    model_list=["gpt-3.5-turbo"])

llm_config = {
    "functions": [
        {
            "name": "query",
            "description": "query a local HTTP server",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": [],
            },
        },
    ],
    "config_list": config_list,
    "request_timeout": 120,
}

assistant = AssistantAgent(
    name="chatbot",
    system_message="For coding tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
)

user_proxy = UserProxyAgent(
    "user_proxy", code_execution_config={"work_dir": "coding", "use_docker": True}, human_input_mode="NEVER")

# define functions according to the function desription
from IPython import get_ipython
def exec_query():
    response = requests.get("http://172.17.0.1:8000")
    return f"{response.text}"

# register the functions
user_proxy.register_function(
    function_map={
        "query": exec_query
    }
)

user_proxy.initiate_chat(
    assistant, message="Query the server")
