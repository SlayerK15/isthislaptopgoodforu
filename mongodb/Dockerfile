FROM mongo:4.4

WORKDIR /data
COPY data.csv /data/

CMD ["mongod", "--bind_ip_all"]