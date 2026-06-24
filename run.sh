 #!/bin/bash
 xhost +local:docker

 # Check if the container is already running
 if [ $(docker ps -q -f name=noteapp_container) ]; then
     echo "Noteapp is already running."
 else
     echo "Starting Noteapp..."
     docker-compose up -d
 fi
