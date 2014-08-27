# -*- coding: utf-8 -*-

"""popper.popper: provides entry point main()."""

__version__ = "0.1"

import sys
import json
import logging
import os
import SimpleHTTPServer
import SocketServer
import mimetools
from subprocess import call
from _pyio import StringIO

def main( config="/etc/popper/popper.conf", log_file=""):
    
    #Create the log file (if deleted)
    if log_file == "" : 
        if not os.path.isdir("/var/log/popper" ):
            os.mkdir( "/var/log/popper" )
        log_file = "/var/log/popper/popper.log"
        
    if not os.path.isfile( log_file ):
        open( log_file, 'w' )
    
    #Setup Logging
    logging.basicConfig(filename=log_file,
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)
    
    logging.info("Starting Popper")

    #Load the Config File
    try:
        loaded_config = open(config).read()
    except IOError as e:
        logging.error("Config File %s could not be loaded" % config )
        sys.exit()
    
    #Load the Config File
    try:        
        global_config = json.loads( loaded_config )
    except ValueError as e:
        logging.error("Config File %s could not be processed." % config )
        sys.exit()
        
    #Get Config Vars
    try:
        hostname = global_config['hostname']
        port = global_config['port']
        deployments = global_config['deployments']
    except TypeError:
        logging.error("Config File %s could not be processed." % config )
        sys.exit()

    #The Main HTTP Handler
    class CustomHttpHandler( SimpleHTTPServer.SimpleHTTPRequestHandler ):
        def do_GET(self):
            self.send_response(400)
        def do_POST(self):
            
            if self.headers.getheader('X-Github-Event') == "push":
                body = self.rfile.read( int(self.headers.get('Content-length', 0)) )
                post_data = json.loads( body )
                
                #Get the Settings from the GH Payload
                branch = post_data['ref'].replace('refs/heads/','')
                repo = post_data['repository']['full_name']
                pusher = post_data['pusher']['name']
                
                deploy = False
                
                # Check Against the Deployment Config
                for deployment in deployments:
                    if deployment['repo'] == repo and deployment['branch'] == branch:
                        # Get the Deployment Settings
                        tmp_path = "/tmp/pop-pull"
                        destination = deployment['destination']
                        
                        #Recreate temp directory
                        if os.path.isdir(tmp_path):
                            call( [ "rm", "-r", tmp_path ])
                            
                        os.mkdir( tmp_path )
                        
                        #Get the Tar Names
                        remote_tar = "https://github.com/%s/tarball/%s" % (repo, branch) 
                        local_tar = "%s/%s.tar.gz" % ( tmp_path, branch)
                        
                        #Check if the tar should be requested securely
                        if deployment.has_key( 'token' ):
                            call( [ "curl", "-u", "%s:x-oauth-basic" % deployment['token'], "-Lo", local_tar,  remote_tar ] )
                        else:
                            call( [ "curl", "-Lo", local_tar,  remote_tar ] )
                        
                        #Untar Files
                        call( [ "tar", "-xvzf", local_tar , "-C", "%s/" % tmp_path ] )
                        call( [ "rm", local_tar ] )
                        
                        #Rsync to Destination
                        sync_folder = "%s/%s/" % ( tmp_path,  os.listdir( tmp_path )[0] )
                        call( [ "rsync", "-r", sync_folder, "%s/" % destination ])
                        
                        #Remove the Temporary Files
                        call( [ "rm", "-r", tmp_path ])
                        
                        deploy = True
                        logging.info("Sucessful Hook: Repo:%s, Branch:%s, Destination: %s" % (  repo, branch, destination ) )
                            
                        #Run any post commands
                        if deployment.has_key( 'post-commands' ):
                            for command in deployment['post-commands']:
                                logging.info("Running Command: %s" % command )
                                call( command, shell=True )
                            
                if not deploy:
                    logging.warn("Unknown Hook: Repo%s, Branch:%s, From: %s" % (  repo, branch, pusher ) )
                    
                self.send_response(200)
            else:
                self.send_response(400)
    
    #Set up the Server
    httpd = SocketServer.ThreadingTCPServer( ( hostname, int(port) ), CustomHttpHandler )
    logging.info("Serving %s:%s" % (  hostname, port  ) )
    
    #Run the Server
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        logging.info("Server Stopped")
        sys.exit()
