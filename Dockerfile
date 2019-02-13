FROM python:3.6
ARG SECRET_KEY
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash
RUN apt-get install -y nodejs
RUN curl -o- -L https://yarnpkg.com/install.sh | bash 
ENV PATH /root/.yarn/bin:/root/.config/yarn/global/node_modules/:${PATH}
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install --quiet -r requirements.txt
COPY . /code
RUN yarn install
RUN SECRET_KEY=$SECRET_KEY python manage.py collectstatic --noinput -v 0
