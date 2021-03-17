FROM python:3.7.8-buster

RUN pip install flask pyyaml oic gunicorn[gevent]

COPY src /src

WORKDIR /src

# cmd ["python", "app.py", "--host", "0.0.0.0", "--config-path", "/login-config/config.yaml"]

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-k", "gevent", "--workers", "2", "app:create_app(config_path='/login-config/config.yaml')"]
