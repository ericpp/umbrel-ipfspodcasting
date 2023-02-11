import requests
import json

BASEURL="http://kubo:5001"
# BASEURL="http://localhost:5001"

def rpc_request(path: str, params=None):
  return requests.post(BASEURL + path, params=params).json()

def add_file_stream(stream: str, filename):
  files = {'file': (filename, stream)}
  value = requests.post(BASEURL + "/api/v0/add?quiet=true&wrap-with-directory=true", files=files)
  hashes = value.text.split('\n')
  return [
    json.loads(hsh) for hsh in hashes if hsh
  ]

def get_file_size(path):
  response = requests.post(BASEURL + '/api/v0/cat', params={'arg': path}, stream=True)
  size = response.headers['X-Content-Length']
  response.close() # close/ignore file contents
  return size

def add_pin(pin: str):
  return rpc_request("/api/v0/pin/add", {'arg': pin})

def rm_pin(pin: str):
  return rpc_request("/api/v0/pin/rm", {'arg': pin})

def get_ls(path: str):
  return rpc_request("/api/v0/ls", {'arg': path})

def set_config(key: str, value: str):
  params = {'arg': [ key, value ]}

  if value is True or value is False:
    params['json'] = True

  return rpc_request("/api/v0/config", params)

def get_diag_sys():
  return rpc_request("/api/v0/diag/sys")

def get_peer_id():
  value = rpc_request("/api/v0/config?arg=Identity.PeerID")
  return value['Value']

def get_swarm_peers():
  return rpc_request("/api/v0/swarm/peers")

def get_num_peers():
  return len(get_swarm_peers()['Peers'])

def get_repo_stat():
  return rpc_request("/api/v0/repo/stat")

def run_repo_gc():
  return rpc_request("/api/v0/repo/gc?silent=true")
