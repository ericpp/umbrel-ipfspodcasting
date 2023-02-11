#!/usr/bin/python3
import json
import requests
import time
import logging
import os
import ipfs
import io

#Setup Stream Handler (i.e. console)
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler("ipfspodcastnode.log", mode="w")

#Basic logging to ipfspodcastnode.log
logging.basicConfig(
  format="%(asctime)s : %(message)s",
  datefmt="%Y-%m-%d %H:%M:%S",
  handlers=[stream_handler, file_handler],
  level=logging.INFO
)


#Create an empty email.cfg (if it doesn't exist)
if not os.path.exists('cfg/email.cfg'):
  with open('cfg/email.cfg', 'w') as ecf:
    ecf.write('')

#Start WebUI
import webui
logging.info('Starting Web UI')

#Automatically discover relays and advertise relay addresses when behind NAT.
ipfs.set_config('Swarm.RelayClient.Enabled', True)

#Get IPFS ID
peerid = ipfs.get_peer_id()
logging.info('IPFS ID : ' + peerid)

#Main loop
while True:

  #Request payload
  payload = { 'version': 0.6, 'ipfs_id': peerid }

  #Read E-mail Config
  with open('cfg/email.cfg', 'r') as ecf:
    email = ecf.read()
    if email == '':
      email = 'user@example.com'
  payload['email'] = email

  #Check if IPFS is running, restart if necessary.
  payload['online'] = False
  diag = ipfs.get_diag_sys()
  payload['ipfs_ver'] = diag['ipfs_version']
  payload['online'] = diag['net']['online']

  if payload['online'] == False:
    #Start the IPFS daemon
    logging.info('@@@ IPFS NOT RUNNING @@@')

  #Get Peer Count
  payload['peers'] = ipfs.get_num_peers()

  #Request work
  logging.info('Requesting Work...')
  print(payload)
  try:
    response = requests.post("https://IPFSPodcasting.net/Request", timeout=120, data=payload)
    work = json.loads(response.text)
    logging.info('Response : ' + str(work))
  except requests.RequestException as e:
    logging.info('Error during request : ' + str(e))
    work = { 'message': 'Request Error' }

  if work['message'] == 'Request Error':
    logging.info('Error requesting work from IPFSPodcasting.net (check internet / firewall / router).')

  elif work['message'][0:7] != 'No Work':
    if work['download'] != '' and work['filename'] != '':
      logging.info('Downloading ' + str(work['download']))
      #Download any "downloads" and Add to IPFS (1hr48min timeout)
      downhash = None
      with requests.get(work['download'], stream=True, verify=False) as stream:
        print(stream.headers)
        downhash = ipfs.add_file_stream(stream.content, work['filename'])
        downsize = ipfs.get_file_size(downhash[0]['Hash'])
        logging.info('Added to IPFS ( hash : ' + str(downhash[0]['Hash']) + ' length : ' + str(downsize) + ')')
        payload['downloaded'] = downhash[0]['Hash'] + '/' + downhash[1]['Hash']
        payload['length'] = int(downsize)

    if work['pin'] != '':
      #Directly pin if already in IPFS
      logging.info('Pinning hash (' + str(work['pin']) + ')')
      ipfs.add_pin(work['pin'])

      #Verify Success and return full CID & Length
      pinchk = ipfs.get_ls(work['pin'])
      payload['pinned'] = pinchk['Objects'][0]['Links'][0]['Hash'] + '/' + work['pin']
      payload['length'] = pinchk['Objects'][0]['Links'][0]['Size']

    if work['delete'] != '':
      #Delete/unpin any expired episodes
      logging.info('Unpinned old/expired hash (' + str(work['delete']) + ')')
      ipfs.rm_pin(work['delete'])
      payload['deleted'] = work['delete']

    #Report Results
    logging.info('Reporting results...')
    #Get Usage/Available
    repostat = ipfs.get_repo_stat()
    payload['used'] = repostat['RepoSize']
    df = os.statvfs('/')
    payload['avail'] = df.f_bavail * df.f_frsize

    print('result', payload)

    try:
      response = requests.post("https://IPFSPodcasting.net/Response", timeout=120, data=payload)
    except requests.RequestException as e:
      logging.info('Error sending response : ' + str(e))

  else:
    logging.info('No work.')

  #wait 10 minutes then start again
  logging.info('Sleeping 10 minutes...')
  time.sleep(600)
