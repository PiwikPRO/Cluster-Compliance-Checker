FROM alpine:3.16

RUN apk add --no-cache sysstat curl fio

RUN addgroup -S piwikpro && \
	adduser -h /piwikpro -s /bin/nologin -g "Piwik PRO user" -S piwikpro -G piwikpro
USER piwikpro
WORKDIR /piwikpro

CMD [ "tail", "-f", "/dev/null" ]
