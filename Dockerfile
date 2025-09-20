#FROM nexuscoe.rjil.ril.com:5115/jioent/health/jio-python-base:3.8-slim
# FROM devopsartifact.jio.com/jpf-jio_health__dev__dcr/jio-python-base:3.8-slim
FROM rhhdevacr.azurecr.io/jioent/health/base/python/3.12:3.12.11-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

ARG PROXY_HTTP
ARG PROXY_HTTPS
ARG PROXY_NO
ENV http_proxy $PROXY_HTTP
ENV https_proxy $PROXY_HTTPS
ENV no_proxy $PROXY_NO

# setting up pypy feed
COPY pip_config_file .
ENV PIP_CONFIG_FILE "/usr/src/app/pip_config_file"

# Installing requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
RUN opentelemetry-bootstrap -a install

ENV http_proxy ""
ENV https_proxy ""



# Adding remaining files
ADD . .

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "src.main:app"]