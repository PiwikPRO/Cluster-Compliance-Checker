ARG ALPINE_VERSION=3.16
ARG PYTHON_VERSION=3.9
ARG BASE_IMAGE=python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

#############
# Bootstrap #
#############
FROM ${BASE_IMAGE} as bootstrap

WORKDIR /source
RUN apk add npm
COPY package.json package-lock.json /source/
RUN npm install

###############
# Build stage #
###############
FROM ${BASE_IMAGE} as build

WORKDIR /source

# Build dependencies
RUN apk add --no-cache poetry alpine-sdk

# Dependencies only
COPY pyproject.toml poetry.lock /source/
RUN poetry env use ${PYTHON_VERSION} && \
	poetry export --without-hashes --output /tmp/requirements.txt && \
	python -m pip install --ignore-installed --prefix /install -r /tmp/requirements.txt

# Package
COPY cluster_compliance_checker /source/cluster_compliance_checker
RUN poetry build && \
	python -m pip install --prefix /install dist/*.whl

#############
# Run stage #
#############
FROM ${BASE_IMAGE}
LABEL maintainer="Piotr Miszkiel <p.miszkiel@piwik.pro>, Michał Mieszczak <m.mieszczak@piwik.pro>"

WORKDIR /app
ADD statics statics
COPY --from=bootstrap /source/node_modules /app/node_modules
COPY --from=build /install /usr/local

RUN addgroup -S piwikpro && \
	adduser -h /piwikpro -s /bin/nologin -g "Piwik PRO user" -S piwikpro -G piwikpro && \
	mkdir /app/report && \
	chown -R piwikpro:piwikpro /app

USER piwikpro
EXPOSE 8080

ENTRYPOINT [ "cluster-compliance-checker" ]
