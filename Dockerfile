FROM python:3.7
ARG SECRET_KEY
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash
RUN apt-get install -y nodejs
RUN curl -o- -L https://yarnpkg.com/install.sh | bash 
ENV PATH /root/.yarn/bin:/root/.config/yarn/global/node_modules/:${PATH}
RUN mkdir /code
WORKDIR /code
RUN pip install pipenv
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --system
COPY . /code
RUN yarn install
RUN SECRET_KEY=$SECRET_KEY python manage.py collectstatic --noinput -v 0
