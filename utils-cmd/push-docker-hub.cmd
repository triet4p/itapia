@echo off
echo Pushing all docker images to Docker Hub...
docker tag itapia-data-processor:latest trietlm2004/itapia-data-processor:latest 
docker push trietlm2004/itapia-data-processor:latest 

docker tag itapia-data-seeds:latest trietlm2004/itapia-data-seeds:latest 
docker push trietlm2004/itapia-data-seeds:latest 

docker tag itapia-api-gateway:latest trietlm2004/itapia-api-gateway:latest
docker push trietlm2004/itapia-api-gateway:latest

docker tag itapia-ai-service-quick:latest trietlm2004/itapia-ai-service-quick:latest
docker push trietlm2004/itapia-ai-service-quick:latest

docker tag itapia-evo-worker:latest trietlm2004/itapia-evo-worker:latest
docker push trietlm2004/itapia-evo-worker:latest

echo All images push successfully!