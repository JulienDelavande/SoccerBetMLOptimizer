{{/*
Helper function to inject DB_PASSWORD from either a direct value or a secret.
Usage: {{ include "inject_db_password" . }}
*/}}
{{- define "inject_db_password" -}}
- name: DB_PASSWORD
  {{- if .Values.postgresqlGlobal.auth.password }}
  # Option 1: If the password is provided directly in values.yaml
  value: {{ .Values.postgresqlGlobal.auth.password | quote }}
  {{- else if .Values.postgresqlGlobal.auth.existingSecret }}
  # Option 2: If no password is provided, use the secret
  valueFrom:
    secretKeyRef:
      name: {{ .Values.postgresqlGlobal.auth.existingSecret }}
      key: {{ .Values.postgresqlGlobal.auth.secretKeys.userPasswordKey }}
  {{- else }}
  # Error if neither the password nor the secret is provided
  {{- fail "Please provide either postgresqlGlobal.auth.password or postgresqlGlobal.auth.existingSecret in values.yaml" }}
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

