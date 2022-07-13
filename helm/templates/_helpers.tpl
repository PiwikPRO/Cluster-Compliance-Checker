
{{- define "app" -}}
app: {{ printf "%s-%s" $.Release.Name $.Chart.Name | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "chart" -}}
chart: {{ printf "%s-%s" $.Chart.Name $.Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "labels" -}}
{{ include "app" . }}
{{ include "chart" . }}
release: {{ $.Release.Name }}
heritage: {{ $.Release.Service }}
{{- if $.Values.extraLabels }}
{{ $.Values.extraLabels | toYaml }}
{{- end }}
{{- end }}

{{- define "namespace" -}}
{{- if .Values.namespaceOverride -}}
{{- .Values.namespaceOverride -}}
{{- else -}}
{{- .Release.Namespace -}}
{{- end -}}
{{- end -}}

{{- define "tag" -}}
{{- if .Values.docker.tag -}}
{{- .Values.docker.tag -}}
{{- else -}}
{{- $.Chart.Version -}}
{{- end -}}
{{- end -}}
