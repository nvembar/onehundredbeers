FROM python:3.7
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash
RUN apt-get install -y nodejs
RUN curl -o- -L https://yarnpkg.com/install.sh | bash 
ENV PATH /root/.yarn/bin:/root/.config/yarn/global/node_modules/:${PATH}
RUN pip install pipenv
RUN mkdir /code
WORKDIR /code
COPY package.json .
COPY yarn.lock .
RUN yarn install
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --system
COPY . /code
ARG SECRET_KEY
RUN SECRET_KEY=$SECRET_KEY python manage.py collectstatic --noinput -v 0
