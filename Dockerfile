FROM python:3.6
MAINTAINER Samuel Taylor "docker@samueltaylor.org"

# Web requirements
RUN apt-get update && apt-get install -y supervisor nginx
RUN pip install gunicorn

# nginx
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled/nginx.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
COPY config/nginx.conf /etc/nginx/sites-available/
RUN mkdir /logs

# supervisord
ADD config/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# App-specific stuff
ADD rss_filter.py /app/rss_filter.py
ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

EXPOSE 80

CMD ["/usr/bin/supervisord"]
