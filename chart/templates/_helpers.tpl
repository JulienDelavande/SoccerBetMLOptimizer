{{/*
DB_PASSWORD from the database secret (CloudNativePG basic-auth secret).
Usage: {{ include "inject_db_password" . }}
*/}}
{{- define "inject_db_password" -}}
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ required "database.existingSecret is required" .Values.database.existingSecret }}
      key: {{ .Values.database.passwordKey }}
{{- end }}

{{/*
SESSION_SECRET (JWT signing) from a secret, only if configured. Optional so the pod
boots before the account feature's secret exists.
Usage: {{ include "inject_session_secret" . }}
*/}}
{{- define "inject_session_secret" -}}
{{- if .Values.account.sessionSecret.existingSecret }}
- name: SESSION_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.account.sessionSecret.existingSecret }}
      key: {{ .Values.account.sessionSecret.key }}
      optional: true
{{- end }}
{{- end }}

{{/*
Helper function to inject THE_ODDS_API_KEY from either a direct value or un secret.
Usage: {{ include "inject_api_key" . }}
*/}}
{{- define "inject_api_key" -}}
- name: THE_ODDS_API_KEY
  {{- if .Values.services.dataIngestion.apiKeys.theOddsApiKey }}
  # Option 1: If the API key is provided directly in values.yaml
  value: {{ .Values.services.dataIngestion.apiKeys.theOddsApiKey | quote }}
  {{- else if .Values.services.dataIngestion.apiKeys.existingSecret }}
  # Option 2: If no API key is provided, use the secret
  valueFrom:
    secretKeyRef:
      name: {{ .Values.services.dataIngestion.apiKeys.existingSecret }}
      key: {{ .Values.services.dataIngestion.apiKeys.secretKeys.theOddsApiKey }}
  {{- else }}
  # Error if neither the API key nor the secret is provided
  {{- fail "Please provide either services.dataIngestion.apiKeys.theOddsApiKey or services.dataIngestion.apiKeys.existingSecret in values.yaml" }}
  {{- end }}
{{- end }}

{{- define "cdn.configmapChecksum" -}}
{{- $cm := (lookup "v1" "ConfigMap" .Release.Namespace "cdn-nginx-conf") }}
{{- $data := $cm.data | toYaml }}
{{- $data | sha256sum }}
{{- end }}

